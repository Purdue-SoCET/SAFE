from pwn import *

def thread_cxt():
	r = remote('google.com', 80)
	r.send(b'GET /search?q=a&sxsrf=ALeKk03OXTcWSdtSgTqt3eTioxLEjRQy7A%3A1622042547529&source=hp&ei=s2euYITLHNiw5NoPuv6pyAU&iflsig=AINFCbYAAAAAYK51w_I1oCnlxdZcNYMpaOCmCWauR0PH&oq=a&gs_lcp=Cgdnd3Mtd2l6EAMyCQgjECcQRhD5ATIECCMQJzIECCMQJzIFCAAQkQIyCAgAELEDEIMBMggIABCxAxCDATIFCAAQsQMyCAgAELEDEIMBMgsILhCxAxDHARCjAjIICAAQsQMQgwFQuQJYuQJg5AZoAHAAeACAAbUBiAG1AZIBAzAuMZgBAKABAaoBB2d3cy13aXo&sclient=gws-wiz&ved=0ahUKEwjE8Oiu0-fwAhVYGFkFHTp_ClkQ4dUDCAk&uact=5 HTTP/1.0\r\n\r\n')	
	print(r.recvn(800))
thread_cxt()
