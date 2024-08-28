ARG CBO_IMAGE_URL=armdocker.rnd.ericsson.se/proj-ldc/common_base_os_release/sles
ARG CBO_VERSION=6.16.0-13

FROM ${CBO_IMAGE_URL}:${CBO_VERSION}

ARG CBO_VERSION

ARG ARM_URL="https://arm.sero.gic.ericsson.se/artifactory/proj-ldc-repo-rpm-local"
ARG DEV_REPO="$ARM_URL/adp-dev/adp-build-env/$CBO_VERSION"
ARG CBO_REPO="$ARM_URL/common_base_os/sles/$CBO_VERSION"
ARG PERL_REPO="https://download.opensuse.org/repositories/devel:languages:perl/15.5/devel:languages:perl.repo"

RUN zypper addrepo --gpgcheck-strict -f $CBO_REPO COMMON_BASE_OS_SLES_REPO \
    && zypper addrepo --gpgcheck-strict -f $DEV_REPO ADP_DEV_BUILD_ENV_REPO \
    && zypper addrepo --no-gpgcheck --no-check -f $PERL_REPO \
    && zypper --gpg-auto-import-keys refresh -f \
    && zypper install -l -y curl \
    && zypper install -l -y unzip \
    && zypper install -l -y wget \
    && zypper install -l -y sudo \
    && zypper install -l -y openssh \
    && zypper install -l -y rsyslog \
    && zypper install -l -y python \
    && zypper install -l -y cronie \
    && zypper install -l -y java-11-openjdk-headless \
    && zypper install -l -y vim \
    && zypper install -l -y perl-JSON \
    && zypper removerepo "devel_languages_perl" \
    && zypper clean --all

COPY create_user.sh /
COPY genstats-file.zip /genstats_file.zip
COPY setup_genstats.sh /
COPY teardown.sh /
COPY recording_files-23.10.1.zip /
COPY test_scripts/* /test_scripts/

RUN chmod 777 /create_user.sh
RUN chmod 777 /teardown.sh
RUN chmod 777 /setup_genstats.sh

EXPOSE 22

ARG USER_ID=0
ARG USER_NAME="eric-oss-pm-solution"
RUN echo "$USER_ID:x:$USER_ID:0:An Identity for $USER_NAME:/nonexistent:/bin/false" >>/etc/passwd

USER $USER_ID

CMD ["/usr/lib/systemd/systemd"]
