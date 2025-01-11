
with open('pdu.txt', 'r') as file:
    pdu = file.read()

#print(repr(pdu))

pdu_split = pdu.split("+CMGL: ")[1:-1]

[print(repr(e)) for e in pdu_split]
pdu_split = [x.split("\n")[:-1] for x in pdu_split]
print(f"Length: {len(pdu_split[2])}")
print(repr(pdu_split[2]))
'2,1,"",33',
# <index>, <?>, <len> 
