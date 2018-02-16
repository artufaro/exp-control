CFLAGS=-g
LIBS=-lusb -lxml2 -lgmp
INCLUDE=-I/usr/include/libxml2

all:  writetable

writetable: writetable.c
	$(CC) $(INCLUDE) $(CFLAGS) writetable.c $(LIBS) -o writetable
	sudo chown root:root writetable
	sudo chmod 4755 writetable

clean:
	rm  writetable
