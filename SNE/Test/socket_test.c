#include <SAFE_lib.h>
PORT = 3
int main(){
	struct sockaddr_in addrees;	
	fd = socket(AF_INET, SOCK_STREAM,0);	
	address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons( PORT );
	bind(server_fd, (struct sockaddr *)&address, sizeof(address));
	return 0;
}
