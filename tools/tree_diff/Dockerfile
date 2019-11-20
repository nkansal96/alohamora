FROM ubuntu:18.04

ENV GRADLE_VERSION 6.0.1
ENV GRADLE_HOME    /opt/gradle/gradle-${GRADLE_VERSION}
ENV PATH           ${GRADLE_HOME}/bin:${PATH}

WORKDIR /tmp
RUN apt-get update -y && \
    apt-get install -y openjdk-11-jdk wget unzip && \
    wget https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip && \
    unzip -d /opt/gradle gradle-*.zip && \
    gradle -v

WORKDIR /opt/tree_diff
COPY tools/tree_diff /opt/tree_diff
RUN gradle shadowJar

FROM ubuntu:18.04
RUN apt-get update -y && \
    apt-get install -y openjdk-11-jre-headless

WORKDIR /opt/tree_diff
COPY tools/tree_diff/entrypoint.sh /opt/
COPY --from=0 /opt/tree_diff/build/libs/tree_diff-all.jar tree_diff.jar

ENTRYPOINT ["/opt/entrypoint.sh"]
