CC ?= gcc
CFLAGS ?= -O3 -Wall -Wextra -pedantic -Wmissing-prototypes -Wredundant-decls -Wshadow -Wpointer-arith -fPIC
INCLUDES = -I.

SRCS = fips202.c fips203.c fips204.c pqc_core.c
OBJS = $(SRCS:.c=.o)

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    SHARED_EXT := dylib
    LDFLAGS_SHARED := -dynamiclib
else
    SHARED_EXT := so
    LDFLAGS_SHARED := -shared
endif

TARGET = libpqc_core.$(SHARED_EXT)

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS_SHARED) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

