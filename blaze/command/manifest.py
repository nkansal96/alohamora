""" Implements the commands for viewing and manipulating the training manifest """
import os
import json
from urllib.parse import urlparse
from blaze.action import Policy
from blaze.config.environment import EnvironmentConfig
from blaze.evaluator.simulator import Simulator
from blaze.logger import logger as log
from blaze.preprocess.url import Url

from . import command


@command.argument("manifest_file", help="The file path to the saved manifest file from `blaze preprocess`")
@command.argument("--trainable", "-t", help="Only show trainable push groups", action="store_true", default=False)
@command.argument("--verbose", "-v", help="Show more information", action="store_true", default=False)
@command.command
def view_manifest(args):
    """ View the prepared manifest from `blaze preprocess` """
    log.info("loading manifest", manifest_file=args.manifest_file)
    env_config = EnvironmentConfig.load_file(args.manifest_file)

    print("[[ Request URL ]]\n{}\n".format(env_config.request_url))
    print("[[ Replay Dir ]]\n{}\n".format(env_config.replay_dir))
    print("[[ Trainable Groups ]]\n{}\n".format("\n".join(group.name for group in env_config.trainable_push_groups)))
    print("[[ {}Push Groups ]]".format("Trainable " if args.trainable else ""))

    for group in env_config.push_groups:
        if args.trainable and not group.trainable:
            continue
        print("  [{id}: {name} ({num} resources)]".format(id=group.id, name=group.name, num=len(group.resources)))
        for res in group.resources:
            url = Url.parse(res.url).resource
            if len(url) > 64:
                url = url[:61] + "..."
            print(
                "    {order:<3}  {url:<64}  {type:<6} {size:>8} B  cache: {cache}s  {crit}".format(
                    order=res.order,
                    url=url,
                    type=res.type.name,
                    size=res.size,
                    cache=res.cache_time,
                    crit="critical" if res.critical else "",
                )
            )
        print()

    print("[[ Execution Graph ]]")
    sim = Simulator(env_config)
    sim.print_execution_map()

@command.argument("--manifest_file", help="The file path to the saved manifest file from `blaze preprocess`", required=True)
@command.argument("--trainable", "-t", help="Only show trainable push groups", action="store_true", default=False)
@command.argument("--policy", "-v", help="The policy to compare this manifest to", type=str, required=True)
@command.command
def compare_manifest_to_policy(args):
    """ Get a push policy and see how many urls in it are present in the given manifest 
    This function now does not respect the manifest_file and policy args. 
    needs the urls to be hardcoded
    """

    good_websites = []
    websites = ['about.comenity.net', 'allrecipes.com__', 'archiveofourown.org__', 'archive.org', 'arstechnica.com__', 'bleacherreport.com__', 'bongacams.com__', 'ca.gov__', 'deadspin.com__', 'evernote.com__', 'feedly.com__', 'fivethirtyeight.com__', 'giphy.com__', 'github.com__', 'gizmodo.com__', 'greatergood.com__', 'healthy.kaiserpermanente.org__html__kaiser__index.shtml', 'home.capitalone360.com__', 'imgur.com__', 'investor.vanguard.com__corporate-portal__', 'jalopnik.com__', 'jezebel.com__', 'kinja.com__', 'lifehacker.com__', 'mailchimp.com__about__mcsv__', 'mailchimp.com__', 'medium.com__', 'nymag.com__', 'nypost.com__', 'officedepot.com__', 'order.pizzahut.com__home', 'pages.github.com__', 'patch.com__', 'photobucket.com__', 'products.office.com__en-US__', 'quizlet.com__', 'shareasale.com__', 'slack.com__', 'sprint.com__', 'squareup.com__', 'stackexchange.com__', 'stackoverflow.com__', 'steamcommunity.com__', 'thechive.com__', 'trello.com__', 'vimeo.com__', 'web.mit.edu__', 'www3.hilton.com__en__index.html', 'www.about.com__', 'www.adp.com__', 'www.airbnb.com__', 'www.alibaba.com__', 'www.aliexpress.com__', 'www.amazon.com__', 'www.ancestry.com__', 'www.angieslist.com__', 'www.apple.com__', 'www.ask.com__', 'www.audible.com__', 'www.autotrader.com__', 'www.bankofamerica.com__', 'www.bankrate.com__', 'www.barclaycardus.com__', 'www.barnesandnoble.com__', 'www.bbc.com__', 'www.bbc.co.uk__', 'www.bbt.com__', 'www.bedbathandbeyond.com__', 'www.bestbuy.com', 'www.bodybuilding.com__', 'www.box.com__', 'www.businessinsider.com__', 'www.capitalone.com__', 'www.cargurus.com__', 'www.cars.com__', 'www.cbs.com__', 'www.cbsnews.com__', 'www.cbssports.com__', 'www.change.org__', 'www.chase.com__', 'www.cnbc.com__', 'www.cnet.com__', 'www.cnn.com__', 'www.concursolutions.com__', 'www.constantcontact.com__', 'www.creditkarma.com__', 'www.cvs.com__', 'www.dailykos.com__', 'www.dailymotion.com__us', 'www.dell.com__en-us__', 'www.delta.com', 'www.digitaltrends.com__', 'www.discover.com__', 'www.disney.com__', 'www.dominos.com__en__', 'www.dropbox.com__', 'www.ebay.com', 'www.ecollege.com__', 'www.engadget.com__', 'www.eonline.com__', 'www.espnfc.us__', 'www.etsy.com__', 'www.eventbrite.com__', 'www.fedex.com__', 'www.fitbit.com__', 'www.food.com__', 'www.foodnetwork.com__', 'www.fool.com__', 'www.forbes.com__home_usa__', 'www.foxnews.com__', 'www.foxsports.com__', 'www.gamespot.com__', 'www.gap.com__', 'www.geico.com__', 'www.glassdoor.com__index.htm', 'www.godaddy.com__', 'www.goodhousekeeping.com__', 'www.goodreads.com__', 'www.google.com__', 'www.groupon.com__', 'www.hgtv.com__', 'www.homeaway.com__', 'www.homedepot.com__', 'www.hotnewhiphop.com__', 'www.howtogeek.com__', 'www.icims.com__', 'www.ign.com__', 'www.iheart.com__', 'www.ikea.com', 'www.imdb.com__', 'www.indeed.com__', 'www.independent.co.uk__us', 'www.instagram.com__', 'www.instructables.com__', 'www.intuit.com__', 'www.irs.gov__', 'www.jetblue.com__', 'www.kayak.com__', 'www.khanacademy.org__', 'www.kickstarter.com__', 'www.legacy.com__', 'www.linkedin.com__', 'www.littlethings.com__', 'www.livestrong.com__', 'www.mapquest.com__', 'www.marketwatch.com__', 'www.marriott.com__default.mi', 'www.mayoclinic.org__', 'www.meetup.com__', 'www.microsoft.com__en-us__', 'www.mint.com__', 'www.mozilla.org__en-US__', 'www.msnbc.com__', 'www.navyfederal.org__', 'www.netflix.com__', 'www.nih.gov__', 'www.npr.org__', 'www.ny.gov__', 'www.nytimes.com__', 'www.office.com__', 'www.okcupid.com__', 'www.okta.com__', 'www.pandora.com', 'www.papajohns.com__', 'www.patheos.com', 'www.paypal.com__home', 'www.pch.com__', 'www.pinterest.com__', 'www.pixnet.net__', 'www.playstation.com__en-us__', 'www.pogo.com__', 'www.pornhub.com__', 'www.priceline.com__', 'www.qualtrics.com__', 'www.qvc.com__', 'www.reddit.com__', 'www.redfin.com__', 'www.redtube.com__', 'www.refinery29.com__', 'www.regions.com__personal-banking__', 'www.rei.com__', 'www.roblox.com__', 'www.rollingstone.com__', 'www.rottentomatoes.com__', 'www.salesforce.com__', 'www.samsclub.com__sams__', 'www.schwab.com__', 'www.searchincognito.com__', 'www.sears.com__', 'www.shutterfly.com__', 'www.shutterstock.com__', 'www.si.com__', 'www.slate.com__', 'www.slideshare.net__', 'www.smugmug.com__', 'www.southwest.com__', 'www.speedtest.net__', 'www.spotify.com__us__', 'www.squarespace.com__', 'www.ssa.gov__', 'www.starbucks.com__', 'www.state.gov__index.htm', 'www.surveymonkey.com__', 'www.swagbucks.com__', 'www.taboola.com__', 'www.target.com', 'www.telegraph.co.uk__', 'www.texas.gov', 'www.theblaze.com__', 'www.thedailybeast.com__', 'www.theguardian.com__us', 'www.thekitchn.com__', 'www.theodysseyonline.com__', 'www.thesaurus.com__', 'www.theverge.com__', 'www.timeanddate.com__', 'www.t-mobile.com__', 'www.tomshardware.com__', 'www.twcc.com__', 'www.twitch.tv__', 'www.ups.com__', 'www.urbandictionary.com__', 'www.usbank.com__index.html', 'www.usps.com__', 'www.vice.com__en_us', 'www.vox.com__', 'www.walgreens.com__', 'www.washingtonpost.com__', 'www.wayfair.com__', 'www.webex.com__', 'www.webmd.com__', 'www.weebly.com__', 'www.wellsfargo.com__', 'www.whitepages.com__', 'www.wikihow.com__Main-Page', 'www.wix.com__', 'www.wunderground.com__', 'www.xfinity.com__', 'www.yahoo.com__', 'www.yellowpages.com__', 'www.yelp.com__', 'www.youporn.com__']
    #websites = ['www.nytimes.com__']
    website_to_accuracy = {}
    for website_name in websites:
        policy = get_policy_file_path(website_name)
        manifest_file = get_manifest_file_path(website_name)
        if not os.path.exists(manifest_file):
            continue
        log.info("loading manifest", manifest_file=manifest_file)
        env_config = EnvironmentConfig.load_file(manifest_file)
        list_of_urls_in_manifest = []
        for group in env_config.push_groups:
            if args.trainable and not group.trainable:
                continue
            for res in group.resources:
                list_of_urls_in_manifest.append(res.url)
        list_of_urls_in_policy = []
        try:
            with open(policy, "r") as policy_file:
                policy_dict = json.load(policy_file)
        except json.JSONDecodeError as e:
            print("failed to decode json for " + policy + ", err: " + str(e), file=sys.stderr)
            continue
        except FileNotFoundError as e:
            print("failed to load website policy for " + policy + ", err: " + str(e))
        policy = Policy.from_dict(policy_dict)
        for ptype, policy_obj in policy_dict.items():
            if ptype == "push" or ptype == "preload":
                for (source, deps) in policy_obj.items():
                    list_of_urls_in_policy.append(source)
                    for obj in deps:
                        list_of_urls_in_policy.append(obj["url"])
        list_of_urls_in_policy = list(set(list_of_urls_in_policy))
        list_of_urls_in_manifest = list(set(list_of_urls_in_manifest))
        
        list_of_urls_in_policy = [urlparse(l).path for l in list_of_urls_in_policy]
        list_of_urls_in_manifest = [urlparse(l).path for l in list_of_urls_in_manifest]
        print(f'set of urls in policy is ${list_of_urls_in_policy}')
        print(f'set of urls in manifest is ${list_of_urls_in_manifest}')
        num_of_urls_in_policy_but_not_in_manifest = 0
        for u in list_of_urls_in_policy:
            if u not in list_of_urls_in_manifest:
                num_of_urls_in_policy_but_not_in_manifest += 1

        print(f'number of urls in manifest:{len(list_of_urls_in_manifest)}')
        print(f'number of urls in policy:{len(list_of_urls_in_policy)}')
        print(f'number of urls in policy but not in manifest:{num_of_urls_in_policy_but_not_in_manifest}')
        print(f'percentage effectiveness of policy is {num_of_urls_in_policy_but_not_in_manifest * 100.0 / len(list_of_urls_in_policy)}')
        website_to_accuracy[website_name] = 100 - (num_of_urls_in_policy_but_not_in_manifest * 100.0 / len(list_of_urls_in_policy))
        # if 100 - (num_of_urls_in_policy_but_not_in_manifest * 100.0 / len(list_of_urls_in_policy)) > 75 and len(list_of_urls_in_policy) > 3:
        #     good_websites.append(website_name)
        fraction_of_useless_urls = (num_of_urls_in_policy_but_not_in_manifest / len(list_of_urls_in_policy))
        if fraction_of_useless_urls < 0.25:
            good_websites.append(website_name)
    # print(json.dumps(website_to_accuracy, indent=4))
    print(good_websites)

def get_manifest_file_path(website_name):
    return "/home/murali/Documents/real_world/manifests/april_2020_real_world_only_manifest_only_new_manifests/"  + website_name.replace("/","__") + ".manifest" 
    #return "/home/murali/Documents/new_si_new_plt_manifests/april_2020_new_si_new_plt_manifests/" + website_name.replace("/","__") + ".manifest" 

def get_policy_file_path(website_name):
    policy_path = "/home/murali/Documents/real_world/alohamora_policies_using_old_sites/14_79_2/" + website_name.replace("/","__") +  "14000_79_2.json"
    print(f'returning {policy_path}')
    return policy_path

@command.command
def compare_manifest_to_policy_for_a_set(args):
    websites = ['www.bedbathandbeyond.com__']
    myargs = {}
    for website_name in websites:
        myargs["policy"]=get_policy_file_path(website_name),
        myargs["manifest_file"]=get_manifest_file_path(website_name)
        result[x] = compare_manifest_to_policy(myargs)



@command.argument("manifest_file", help="The manifest file to update")
@command.argument("--replay_dir_path_prefix", help="Update the path prefix of the replay directory")
@command.argument("--replay_dir_folder_name", help="Update the folder name of replay directory")
@command.argument(
    "--save_as",
    help="Save the manifest in the specified location, making a copy of the original. "
    "This option does not modify the original manifest",
)
@command.argument("--train_domain_globs", nargs="*", help="The glob patterns of domain names to enable training for")
@command.command
def update_manifest(args):
    """
    Update the manifest file with the specified changes. This will replace the manifest file with the
    update version, unless --save_as is specified, in which case it will create a new manifest file in
    that location and leave the original one unmodified.
    """
    save_as = args.save_as or args.manifest_file
    log.info(
        "Updating manifest",
        manifest_file=args.manifest_file,
        replay_dir_path_prefix=args.replay_dir_path_prefix,
        replay_dir_folder_name=args.replay_dir_folder_name,
        save_as=save_as,
    )
    env_config = EnvironmentConfig.load_file(args.manifest_file)

    new_replay_dir = env_config.replay_dir
    if args.replay_dir_path_prefix:
        new_replay_dir = os.path.join(args.replay_dir_path_prefix, os.path.basename(new_replay_dir))

    if args.replay_dir_folder_name:
        new_replay_dir = os.path.join(os.path.dirname(new_replay_dir), args.replay_dir_folder_name)

    new_env_config = env_config._replace(replay_dir=new_replay_dir)
    new_env_config.save_file(save_as)
