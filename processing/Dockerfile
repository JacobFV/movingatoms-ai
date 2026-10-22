# syntax=docker/dockerfile:1.7
# Moving Atoms processing worker: scan ingest (decode, label, Potree layers, pictures) and the model jobs.
#
#   docker build -t ma-proc .                                   # this machine's architecture
#   docker build --platform linux/amd64 -t ma-proc:amd64 .      # e.g. Cloudflare Containers, from an arm64 host
#   docker run --rm -e WORKER_TOKEN=… -e MA_SITE=https://movingatoms-ai.pages.dev ma-proc
#
# Everything is built in a stage on the BUILD machine's own architecture: PotreeConverter is cross-compiled and the
# Python packages are installed from wheels for the TARGET platform, so no foreign binary ever runs during the build
# (QEMU emulation of amd64 on arm64 hosts is unreliable). The final stage only copies files.
# Debian trixie (glibc 2.41): IfcOpenShell's aarch64 wheels need glibc 2.38+.
ARG PYTHON=3.12-slim-trixie

FROM --platform=$BUILDPLATFORM python:${PYTHON} AS build
ARG TARGETARCH BUILDARCH
ARG POTREE_COMMIT=d9387d52807bf8936fe98096b9992ea13b50ba94
COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /usr/local/bin/uv
RUN set -eux; \
    case "$TARGETARCH" in amd64) T=x86_64-linux-gnu ;; arm64) T=aarch64-linux-gnu ;; *) echo "unsupported $TARGETARCH"; exit 1 ;; esac; \
    echo "$T" > /triplet; \
    apt-get update; \
    apt-get install -y --no-install-recommends build-essential cmake git ca-certificates file; \
    if [ "$TARGETARCH" = "$BUILDARCH" ]; then \
      apt-get install -y --no-install-recommends libtbb-dev libxerces-c-dev; \
    else \
      dpkg --add-architecture "$TARGETARCH"; apt-get update; \
      apt-get install -y --no-install-recommends "crossbuild-essential-$TARGETARCH" "libtbb-dev:$TARGETARCH"; \
    fi; \
    rm -rf /var/lib/apt/lists/*

# PotreeConverter 2.1.1 for the target (libstdc++/libgcc linked statically; libtbb shipped beside it)
RUN set -eux; T=$(cat /triplet); \
    git clone https://github.com/potree/PotreeConverter.git /src; cd /src; git checkout "$POTREE_COMMIT"; \
    if [ "$TARGETARCH" = "$BUILDARCH" ]; then X=""; else \
      X="-DCMAKE_SYSTEM_NAME=Linux -DCMAKE_SYSTEM_PROCESSOR=${T%%-*} -DCMAKE_C_COMPILER=$T-gcc -DCMAKE_CXX_COMPILER=$T-g++ \
         -DCMAKE_FIND_ROOT_PATH=/usr/lib/$T -DTBB_DIR=/usr/lib/$T/cmake/TBB"; fi; \
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXE_LINKER_FLAGS="-static-libstdc++ -static-libgcc" $X; \
    cmake --build build -j"$(nproc)"; \
    mkdir -p /out/bin /out/lib; install -m 0755 build/PotreeConverter /out/bin/; \
    cp -a /usr/lib/$T/libtbb.so.12* /out/lib/; \
    find build -name '*.so*' -exec cp -a {} /out/lib/ \; ; \
    file /out/bin/PotreeConverter

# the Python packages, for the target
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN set -eux; T=$(cat /triplet); \
    uv export --frozen --no-dev --no-hashes --no-emit-project > /req.txt; \
    if [ "$TARGETARCH" = "$BUILDARCH" ]; then \
      uv pip install --python /usr/local/bin/python3 --target /opt/site --compile-bytecode -r /req.txt; \
      # pye57 has no aarch64 wheel: it was compiled here against Xerces-C; ship its shared libraries
      for so in $(find /opt/site -name '*.so'); do ldd "$so" 2>/dev/null | awk '/=> \//{print $3}'; done | sort -u \
        | grep -vE '/(libc|libm|libdl|librt|libpthread|ld-linux[^/]*|libstdc\+\+|libgcc_s|libz|libpython[^/]*)\.so' \
        | grep -v '^/opt/site' | xargs -r cp -L -t /out/lib/; \
    else \
      uv pip install --target /opt/site --python-platform "${T%%-*}-manylinux_2_31" --python-version 3.12 --only-binary :all: -r /req.txt; \
    fi
COPY ma_proc ./ma_proc
RUN mkdir -p /out/work

FROM python:${PYTHON}
COPY --from=build /out/bin/PotreeConverter /usr/local/bin/PotreeConverter
COPY --from=build /out/lib/ /usr/local/lib/ma-proc/
COPY --from=build /opt/site /opt/site
COPY --from=build /app/ma_proc /app/ma_proc
COPY --from=build --chown=10001:10001 /out/work /work
ENV PYTHONPATH=/opt/site:/app PATH=/opt/site/bin:$PATH LD_LIBRARY_PATH=/usr/local/lib/ma-proc \
    PYTHONUNBUFFERED=1 POTREE_CONVERTER=/usr/local/bin/PotreeConverter MA_WORK_DIR=/work
# uid 10001: a host directory mounted at /work must be writable by it (chown 10001:10001)
USER 10001:10001
WORKDIR /app
ENTRYPOINT ["python", "-m", "ma_proc.runner"]
