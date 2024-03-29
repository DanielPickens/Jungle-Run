ARG BASE_IMAGE_NAME=debian:bullseye-slim

# Intermediate build container
FROM $BASE_IMAGE_NAME AS builder

# Set Python and Pip versions
ENV PYTHON_VERSION=3.10.0
ENV PYTHON_PIP_VERSION=21.3.1

ENV GPG_KEY=A035C8C19219BA821ECEA86B64E628F8D684696D
# https://github.com/pypa/get-pip
ENV PYTHON_GET_PIP_URL https://raw.githubusercontent.com/pypa/get-pip/${PYTHON_PIP_VERSION}/public/get-pip.py
ENV PYTHON_GET_PIP_SHA256=c518250e91a70d7b20cceb15272209a4ded2a0c263ae5776f129e0d9b5674309

ARG BASE_IMAGE_NAME
RUN echo "Using base image \"${BASE_IMAGE_NAME}\" to build Python ${PYTHON_VERSION}"

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN set -e && \
	apt-get update && apt-get install --assume-yes --no-install-recommends \
		ca-certificates \
		dirmngr \
		dpkg-dev \
		gcc \
		gnupg \
		libbz2-dev \
		libc6-dev \
		libexpat1-dev \
		libffi-dev \
		liblzma-dev \
		libsqlite3-dev \
		libssl-dev \
		make \
		netbase \
		uuid-dev \
		wget \
		xz-utils \
		zlib1g-dev

# Download Python source and verify signature with GPG
RUN wget --no-verbose --output-document=python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz" \
	&& wget --no-verbose --output-document=python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc" \
	&& export GNUPGHOME="$(mktemp -d)" \
	&& gpg --batch --keyserver keys.openpgp.org --recv-keys "$GPG_KEY" \
	&& gpg --batch --verify python.tar.xz.asc python.tar.xz \
	&& { command -v gpgconf > /dev/null && gpgconf --kill all || :; } \
	&& rm -rf "$GNUPGHOME" python.tar.xz.asc \
	&& mkdir -p /usr/src/python \
	&& tar -xJC /usr/src/python --strip-components=1 -f python.tar.xz \
	&& rm python.tar.xz

# Compile Python source
RUN cd /usr/src/python \
	&& gnuArch="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)" \
	&& ./configure \
		--build="$gnuArch" \
		--prefix="/python" \
		--enable-loadable-sqlite-extensions \
		--enable-optimizations \
		--enable-ipv6 \
		--disable-shared \
		--with-system-expat \
		--with-system-ffi \
		--without-ensurepip \
	&& make -j "$(nproc)" LDFLAGS="-Wl,--strip-all" \
	&& make install

# Install pip
RUN set -ex; \
	\
	wget --no-verbose --output-document=get-pip.py "$PYTHON_GET_PIP_URL"; \
	echo "$PYTHON_GET_PIP_SHA256 *get-pip.py" | sha256sum --check --strict -; \
	\
	/python/bin/python3 get-pip.py \
		--disable-pip-version-check \
		--no-cache-dir \
		"pip==$PYTHON_PIP_VERSION" "wheel"

# Remove unecessary libraries
RUN find /python/lib -type d -a \( \
		-name __pycache__ -o \
		-name test -o \
		-name tests -o \
		-name idlelib -o \
		-name idle_test -o \
		-name turtledemo -o \
		-name pydoc_data -o \
		-name tkinter \) \
		-exec rm -rf '{}' +

RUN find /python/lib -type f -a \( \
		-name '*.a' -o \
		-name '*.pyc' -o \
		-name '*.pyo' -o \
		-name '*.exe' \) \
		-exec rm '{}' +

# App container
FROM $BASE_IMAGE_NAME AS app

ENV LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=true

# Create symlinks that are expected to exist
RUN ln -s /python/bin/python3-config /usr/local/bin/python-config && \
	ln -s /python/bin/python3 /usr/local/bin/python && \
	ln -s /python/bin/python3 /usr/local/bin/python3 && \
	ln -s /python/bin/pip3 /usr/local/bin/pip && \
	ln -s /python/bin/pip3 /usr/local/bin/pip3 && \
	# Install dependencies
	apt-get update && \
	apt-get install --assume-yes --no-install-recommends ca-certificates libexpat1 libsqlite3-0 libssl1.1 && \
	apt-get purge --assume-yes --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
	rm -rf /var/lib/apt/lists/*

# Copy Python files
COPY --from=builder /python /python

CMD ["python3"]
