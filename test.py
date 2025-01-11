
with open('pdu.txt', 'r') as file:
    pdu = file.read()

[print(x) for x in pdu.split("\n")]

def status(status):
    match status:
        case "0":
            return "REC UNREAD"
        case "1":
            return "REC READ"
        case "2":
            return "STO UNSENT"
        case "3":
            return "STO SENT"

#print(repr(pdu))

pdu_split = pdu.split("+CMGL: ")[1:-1]

[print(repr(e)) for e in pdu_split]
pdu_split = [x.split("\n")[:-1] for x in pdu_split]
print(f"Length: {len(pdu_split[2])}")
print(repr(pdu_split[2]))
'2,1,"",33',
# <index>, <message status (0=unread, 1=read, 2=stored unsent, 3=stored sent)>, <len> 
msg_head = pdu_split[0][0].split(",")
msgs = []
for pdu in pdu_split:
    msg_head = pdu[0].split(",")
    msg_idx = msg_head[0]
    print(msg_idx)
    msg_status = status(msg_head[1])
    msg_len = msg_head[3]
    pdu_encoded = pdu[1]
    pdu_decoded = bytes.fromhex(pdu_encoded).decode('latin-1')
    print(pdu_decoded)
    msgs.append({
        "message_index": msg_idx,
        "message_type": msg_status,
        "message_length": msg_len,
        "pdu_endcoded": pdu_encoded,
        })

[print(msg) for msg in msgs]

print(repr(msg_head))
