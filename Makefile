CC = gcc
CFLAGS = -O2
LDFLAGS = -lm

stsp: stsp.o
	$(CC) $(CFLAGS) -o stsp stsp.o $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@	

clean:
	rm -f stsp *.o

.PHONY: test
test: stsp
	@echo "[test] Running STSP deterministic output check in test/"
	@cd test \
	&& rm -f test-l_lcout.txt test-l_errstsp.txt test-l_vis.txt .stsp_test_first.txt \
	&& ../stsp test-l.in \
	&& cp test-l_lcout.txt .stsp_test_first.txt \
	&& cmp -s test-l_lcout.txt test-l_lcout.expected.txt || { echo "[test] Mismatch vs reference after first run" >&2; exit 1; } \
	&& ../stsp test-l.in \
	&& cmp -s test-l_lcout.txt test-l_lcout.expected.txt || { echo "[test] Mismatch vs reference after second run" >&2; exit 1; } \
	&& cmp -s test-l_lcout.txt .stsp_test_first.txt || { echo "[test] Mismatch between first and second runs" >&2; exit 1; } \
	&& rm -f .stsp_test_first.txt \
	&& echo "[test] OK: Outputs are stable and match reference."
