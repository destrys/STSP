CC = gcc
CFLAGS = -O2
LDFLAGS = -lm

# Test configuration (override on the command line):
#   make test RUN_STDOUT=/dev/stdout
TEST_DIR ?= test
RUN_STDOUT ?= /dev/null

stsp: stsp.o
	$(CC) $(CFLAGS) -o stsp stsp.o $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@	

clean:
	rm -f stsp *.o

.PHONY: test
test: stsp
	@echo "[test] Running STSP deterministic output check in $(TEST_DIR)/ (stdout -> $(RUN_STDOUT))"
	@cd $(TEST_DIR) \
	&& rm -f test-l_lcout.txt test-l_errstsp.txt test-l_vis.txt .stsp_test_first.txt \
	&& ../stsp test-l.in 1>$(RUN_STDOUT) \
	&& cmp -s test-l_lcout.txt test-l_lcout.expected.txt || { echo "[test] Mismatch vs expected" >&2; exit 1; } \
	&& rm -f .stsp_test_first.txt \
	&& echo "[test] OK: Outputs are stable and match expected."
