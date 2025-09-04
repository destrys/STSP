CC = gcc
CFLAGS = -O2
LDFLAGS = -lm

# Test configuration (override on the command line):
#   make test RUN_STDOUT=/dev/stdout
TEST_DIR ?= test
RUN_STDOUT ?= /dev/null

./bin/stsp: ./src/stsp.o
	$(CC) $(CFLAGS) -o ./bin/stsp ./src/stsp.o $(LDFLAGS)

./src/%.o: ./src/%.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f ./bin/stsp src/*.o

.PHONY: test
test: ./bin/stsp
	@echo "[test] Running STSP deterministic output check in $(TEST_DIR)/ (stdout -> $(RUN_STDOUT))"
	@cd $(TEST_DIR) \
	&& rm -f test-l_lcout.txt test-l_errstsp.txt test-l_vis.txt \
	&& ../bin/stsp test-l.in 1>$(RUN_STDOUT) \
	&& cmp -s test-l_lcout.txt test-l_lcout.expected.txt || { echo "[test] Mismatch vs expected" >&2; exit 1; } \
	&& echo "[test] OK: Outputs are stable and match expected."
