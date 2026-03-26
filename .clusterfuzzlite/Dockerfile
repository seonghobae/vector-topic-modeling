FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:82881adac98febc4a4a8e0c7afef634876d4119c90f0d41eeb4cb5ce51416955

COPY . $SRC/vector-topic-modeling
WORKDIR $SRC/vector-topic-modeling
COPY .clusterfuzzlite/build.sh $SRC/
