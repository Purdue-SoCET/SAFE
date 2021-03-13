#ifndef SAFE_lib
#define SAFE_lib

struct sockaddr {
	sa_family_t	sa_family;	/* address family */
	char		sa_data[14];	/* actually longer; address value */
};

struct msghdr {
	void		*msg_name;		/* optional address */
	socklen_t	 msg_namelen;		/* size of address */
	struct iovec	*msg_iov;		/* scatter/gather array */
	int		 msg_iovlen;		/* # elements in msg_iov */
	void		*msg_control;		/* ancillary data, see below */
	socklen_t	 msg_controllen;	/* ancillary data buffer len */
	int		 msg_flags;		/* flags on received message */
};

typedef int socklen_t;
typedef int size_t;

int	accept(int, struct sockaddr *, socklen_t *);
int	bind(int, const struct sockaddr *, socklen_t);
int	connect(int, const struct sockaddr *, socklen_t);
int	getpeername(int, struct sockaddr *, socklen_t *);
int	getsockname(int, struct sockaddr *, socklen_t *);
int	getsockopt(int, int, int, void *, socklen_t *);
int	listen(int, int);
ssize_t	recv(int, void *, size_t, int);
ssize_t	recvfrc om(int, void *, size_t, int, struct sockaddr *, socklen_t *);
ssize_t	recvmsg(int, struct msghdr *, int);
ssize_t	send(int, const void *, size_t, int);
ssize_t	sendto(int, const void *, size_t, int, const struct sockaddr *, socklen_t);
ssize_t	sendmsg(int, const struct msghdr *, int);
int	sendfile(int, int, off_t, size_t, struct sf_hdtr *, off_t *, int);
int	setsockopt(int, int, int, const void *, socklen_t);
int	shutdown(int, int);
int	socket(int, int, int);
int	socketpair(int, int, int, int *);



#endif

