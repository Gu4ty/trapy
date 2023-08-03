from trapy import close, recv, dial, send
import os

a = [1,2,3]
client = dial("127.0.0.1:6")
if client:
    count = 1
    while True:
        try:
            client_data = open(f"c{count}.txt", "r")
        except FileNotFoundError:
            client_data = open(f"c{count}.txt", "w+")
        else:
            count += 1
            continue
        break
    
    r = recv(client, 30000)
    client_data.write(r.decode("utf8"))
    print(len(r))
    server_data = open("server_data.txt", "r")
    server_data.seek(0)
    client_data.seek(0)

    sd = server_data.read()
    cd = client_data.read()
    broke = False
    if len(sd) != len(cd) and len(sd) > 1:
        print("Files have different lens")
        broke = True
        sd = sd[:len(cd)]
    count2 = 1
    for i, j in zip(sd, cd):
        count2 += 1
        if i != j:
            print("Different bytes:",i,"!=",j, "position:",count2)
            broke = True        
    if not broke:
        print("Succes")            

    close(client)
    client_data.close()
    server_data.close()
    input(f"Press enter to erase c{count}.txt")
    os.remove(f"c{count}.txt")
    


