import itertools

class Results(object):
  def __init__(self, res):
    self.first_contentful_paint = res['firstContentfulPaint']
    self.first_meaningful_paint = res['firstMeaningfulPaint']
    self.time_to_interactive = res['interactive']
    self.first_cpu_idle = res['firstCPUIdle']
    self.speed_index = res['speedIndex']
  
  def __repr__(self):
    return 'ResultSet<{}>'.format(' '.join(itertools.starmap('{}={}'.format, vars(self).items())))
