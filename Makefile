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
	@echo "[test] Running Python vs C parity checks in test/ (stdout -> $(RUN_STDOUT))"
	@set -e; \
	cd test ; \
	PATH=../bin:$$PATH PYTHONPATH=.. python3 run_l.py 1>$(RUN_STDOUT) \
	  && rm -f test-l_errstsp.txt test-l_vis.txt test-l_lcout.txt \
	  && ../bin/stsp test-l.in 1>$(RUN_STDOUT) \
	  && cmp -s test-l_lcout.txt pyact-l_lcout.txt \
	  && echo "[test] OK: Python L matches C." ; \
	  s1=$$?; \
	PATH=../bin:$$PATH PYTHONPATH=.. python3 run_m.py 1>$(RUN_STDOUT) \
	  && rm -f test-M_errstsp.txt test-M_parambest.txt test-M_lcbest.txt test-M_mcmc.txt test-M_vis.txt test-M_finalparam.txt \
	  && ../bin/stsp test-M.in 1>$(RUN_STDOUT) \
	  && cmp -s test-M_finalparam.txt pyact-m_finalparam.txt \
	  && echo "[test] OK: Python M matches C." ; \
	  s2=$$?; \
	PATH=../bin:$$PATH PYTHONPATH=.. python3 run_s.py 1>$(RUN_STDOUT) \
	  && rm -f test-s_errstsp.txt test-s_parambest.txt test-s_lcbest.txt test-s_mcmc.txt test-s_vis.txt test-s_finalparam.txt \
	  && ../bin/stsp test-s.in 1>$(RUN_STDOUT) \
	  && cmp -s test-s_finalparam.txt pyact-s_finalparam.txt \
	  && echo "[test] OK: Python s matches C." ; \
	  s3=$$?; \
	if [ $$s1 -ne 0 ] || [ $$s2 -ne 0 ] || [ $$s3 -ne 0 ]; then \
	    echo "[test] Python parity FAILED" >&2; exit 1; \
	else \
	    echo "[test] Python parity OK"; \
	fi
