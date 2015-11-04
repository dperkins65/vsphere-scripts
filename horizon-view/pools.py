#!/usr/bin/python
#
# Daniel Perkins (dperkins65@github.com)
#
# A demonstration on how to retrieve desktop pools
# using the View server's LDAP interface.
#
# Prerequisites:
#   ldap3
#

from ldap3 import Server, Connection, SIMPLE, SYNC, ALL, NTLM

server_address = input("View server address --> ")
username = input("Username --> ")
password = input("Password --> ")

# Auth with Windows domain creds
server = Server(server_address, get_info=ALL)
conn = Connection(server, user=username, password=password, authentication=NTLM, auto_bind=True)

# To view the schema, uncomment the following
#print(server.schema)

# Search for Server Pool class
conn.search('dc=vdi, dc=vmware, dc=int', '(objectClass=pae-serverpool)', attributes=['pae-DisplayName', 'pae-VmResourcePool', 'pae-MemberDN', 'pae-VmDatastore', 'pae-VmPath']) 
print(conn.entries)

