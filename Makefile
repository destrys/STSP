CC = gcc
CFLAGS = -O2
LDFLAGS = -lm

stsp: stsp.o
	$(CC) $(CFLAGS) -o stsp stsp.o $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@	

clean:
	rm -f stsp *.o
