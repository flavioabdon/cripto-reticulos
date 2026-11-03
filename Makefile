CC ?= gcc
CFLAGS ?= -O3 -Wall -Wextra -pedantic -Wmissing-prototypes -Wredundant-decls -Wshadow -Wpointer-arith -fPIC
INCLUDES = -Isrc/pqc

PQC_SRCS = \
	src/pqc/fips202.c \
	src/pqc/fips203.c \
	src/pqc/fips204.c \
	src/pqc/pqc_core.c

ALL_SRCS = $(PQC_SRCS)
ALL_OBJS = $(ALL_SRCS:.c=.o)

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    SHARED_EXT := dylib
    LDFLAGS_SHARED := -dynamiclib
else
    SHARED_EXT := so
    LDFLAGS_SHARED := -shared
endif

LIB_TARGET = src/pqc/libpqc_core.$(SHARED_EXT)

.PHONY: all build clean kat tamarin test

all: build

build: $(LIB_TARGET)

$(LIB_TARGET): $(ALL_OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS_SHARED) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

test: build
	python3 -m unittest discover -s tests -p "test_*.py"

kat: build
	python3 validacion/kat/runner_kat.py

tamarin:
	tamarin-prover --prove tamarin/protocolo.spthy

clean:
	rm -f $(ALL_OBJS) $(LIB_TARGET) validacion/kat/*.o validacion/kat/test_kat_*
