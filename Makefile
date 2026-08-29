CC ?= gcc
CFLAGS ?= -O3 -Wall -Wextra -pedantic -Wmissing-prototypes -Wredundant-decls -Wshadow -Wpointer-arith -fPIC
INCLUDES = -Isrc/pqc -Isrc/pqc/pqclean/common -Isrc/pqc/pqclean/crypto_kem/ml-kem-768/clean -Isrc/pqc/pqclean/crypto_sign/ml-dsa-65/clean

COMMON_SRCS = \
	src/pqc/pqclean/common/fips202.c \
	src/pqc/pqclean/common/randombytes.c \
	src/pqc/pqclean/common/aes.c \
	src/pqc/pqclean/common/sha2.c \
	src/pqc/pqclean/common/sp800-185.c \
	src/pqc/pqclean/common/nistseedexpander.c

MLKEM_SRCS = \
	src/pqc/pqclean/crypto_kem/ml-kem-768/clean/cbd.c \
	src/pqc/pqclean/crypto_kem/ml-kem-768/clean/indcpa.c \
	src/pqc/pqclean/crypto_kem/ml-kem-768/clean/kem.c \
	src/pqc/pqclean/crypto_kem/ml-kem-768/clean/ntt.c \
	src/pqc/pqclean/crypto_kem/ml-kem-768/clean/poly.c \
	src/pqc/pqclean/crypto_kem/ml-kem-768/clean/polyvec.c \
	src/pqc/pqclean/crypto_kem/ml-kem-768/clean/reduce.c \
	src/pqc/pqclean/crypto_kem/ml-kem-768/clean/symmetric-shake.c \
	src/pqc/pqclean/crypto_kem/ml-kem-768/clean/verify.c

MLDSA_SRCS = \
	src/pqc/pqclean/crypto_sign/ml-dsa-65/clean/ntt.c \
	src/pqc/pqclean/crypto_sign/ml-dsa-65/clean/packing.c \
	src/pqc/pqclean/crypto_sign/ml-dsa-65/clean/poly.c \
	src/pqc/pqclean/crypto_sign/ml-dsa-65/clean/polyvec.c \
	src/pqc/pqclean/crypto_sign/ml-dsa-65/clean/reduce.c \
	src/pqc/pqclean/crypto_sign/ml-dsa-65/clean/rounding.c \
	src/pqc/pqclean/crypto_sign/ml-dsa-65/clean/sign.c \
	src/pqc/pqclean/crypto_sign/ml-dsa-65/clean/symmetric-shake.c

WRAPPER_SRCS = src/pqc/pqc_core.c

ALL_SRCS = $(COMMON_SRCS) $(MLKEM_SRCS) $(MLDSA_SRCS) $(WRAPPER_SRCS)
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
