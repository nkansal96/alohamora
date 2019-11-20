FROM ubuntu:18.04

RUN apt-get update -y && \
    apt-get install -y openjdk-11-jdk gradle

WORKDIR /opt/tree_diff
COPY tools/tree_diff /opt/tree_diff
RUN gradle shadowJar

FROM ubuntu:18.04
RUN apt-get update -y && \
    apt-get install -y openjdk-11-jre-headless

WORKDIR /opt/tree_diff
COPY --from=0 /opt/tree_diff/build/libs/tree_diff-all.jar tree_diff.jar

ENTRYPOINT ["/opt/entrypoint.sh"]
