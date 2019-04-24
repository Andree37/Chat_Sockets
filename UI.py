"""
 Implements an UI that communicates with a client via commands of strings. It has to be attached to a Client that can
 take care of the commands on both sides

 Daniel Afonso - 170221004
 André Ribeiro - 170221006

"""

import tkinter
from client import Client
from threading import Thread
import time
from tkinter.filedialog import askopenfilename

# initial variables


ui_version = "Chat Service UI v1.3"  # 21/04/19 last edit
client = Client()


# Re-establishes a broken connection between the client and server
def reconnect_to_server():
    try:
        # Rebuilds connection
        client.open_client()
        client.connect_to_server("" + username.get())
        new_client_thread = Thread(target=client.run, args=[receive_message])
        new_client_thread.start()
        send_message(client.send_messages)
        new_client_room_thread = Thread(target=client.get_client_room_list, args=[])
        new_client_room_thread.start()
        # UI updates
        labelUser.config(bg="green")
        entry_field.config(state='normal')
        send_button.config(state='normal')
        send_image_button.config(state='normal')
        subMenu1.entryconfig("Exit from server", state="normal")
        subMenu1.entryconfig("Reconnect to server", state="disable")
        label_failed_reconnection.config(text="")
    except ConnectionRefusedError:
        print("Try again")
        subMenu1.entryconfig("Reconnect to server", state="normal")
        label_failed_reconnection.pack()
        label_failed_reconnection.config(text="Connection to the server was not possible!!!")


# Validates the input in the login window, and checks if a connection is possible
def validate_user(event):
    label_failed_connection.config(text="")
    input_username = entry_username.get().strip()
    if input_username is "":
        username.set("")
        label_empty_username.config(text="Please INSERT a username!!!")
    else:
        label_empty_username.config(text="")
        # Connection to server is tried
        try:
            client.connect_to_server("" + input_username)
            login.destroy()
        except ConnectionRefusedError:
            label_failed_connection.pack()
            label_failed_connection.config(text="Connection to the server was not possible!!!")


# Breaks the connection securely and closes the UI
def exit_from_ui():
    client.close_client()
    time.sleep(1)
    main.destroy()


# In case the login window closes abruptly
def check_bad_login():
    bad_login.set("Failed")
    login.destroy()


# Updates the room list with the client names from within the same room, displaying also the rooms name
def update_room_list(room_list):
    room_users_list.delete(0, "end")
    room_split = room_list.split("->")
    current_room.set("" + room_split[0])
    labelRoom.config(text="IN chat room:" + current_room.get())
    labelRoom.pack()
    room_clients = room_split[1]
    room_list_split = room_clients.split("\n")
    for i in room_list_split:
        room_users_list.insert(tkinter.END, i)


# Sends the user input to client
def send_message(client_send):
    entry_feed = entry_field.get()
    message_to_send.set("")
    client_send(entry_feed)
    if entry_feed == "/exit":
        labelUser.config(bg="red")
        exit_from_ui()


# Receives the clients output
def receive_message(msg, list_message=None):
    message_split = msg.split("->")
    if message_split[0] == "update_room_list":
        update_room_list(message_split[1] + "->" + message_split[2])
    elif msg == "RIP":  # Server sided disconnection
        labelUser.config(bg="red")
        entry_field.config(state='disabled')
        send_button.config(state='disabled')
        send_image_button.config(state='disabled')
        msg_list.insert(tkinter.END, "Server connection broke from server side")
        room_users_list.delete(0, "end")
        labelRoom.config(text="IN chat room:")
        labelRoom.pack()
        subMenu1.entryconfig("Reconnect to server", state="normal")
        subMenu1.entryconfig("Exit from server", state="disable")
    elif message_split[0] == "receive_image":  # Receives image data and "renders" it
        array = bytearray()
        with open("received_file.png", "wb") as f:
            for i in list_message:
                array += bytes(i)
            f.write(array)
        f.close()
        image = tkinter.PhotoImage(file=f.name)
        msg_list.insert(tkinter.END, image)
        image_list.append(image)
        image_label = tkinter.Label(meme_frame)
        image_label.image = image
        image_label.config(image=image)
        image_label.pack()

    else:
        msg_list.insert(tkinter.END, msg + " \n")


# Opens OS dialog to select image to upload
def load_image():
    filename = tkinter.filedialog.askopenfilename(
        filetypes=(("PNG", "*.png"), ("All Files", "*.*")),
        title="Choose an image."
    )
    if filename != "":
        # Using try in case user types in unknown file or closes without choosing a file.
        try:
            file = open(filename, "r")
            file.close()
            message_to_send.set("/send_image->" + filename)
        except FileNotFoundError:
            print("No file exists")


# Login Window creation
login = tkinter.Tk()
login.geometry("356x150")
login.resizable(0, 0)
login.title(ui_version)
username = tkinter.StringVar()
username.set("")
bad_login = tkinter.StringVar()
# Login Layout
login_frame = tkinter.Frame(login)
login_frame.pack(fill=tkinter.X)
label1 = tkinter.Label(login_frame, text=ui_version, bg="blue", fg="white")
label1.pack(fill=tkinter.X)
signup_frame = tkinter.Frame(login_frame)
signup_frame.pack()
label_request = tkinter.Label(signup_frame, text="Welcome to the chat service")
label_request.pack()
input_setup_frame = tkinter.Frame(signup_frame)
input_setup_frame.pack()
label_request = tkinter.Label(input_setup_frame, text="Username:")
label_request.pack(side=tkinter.LEFT)
#  Warning labels
label_failed_connection = tkinter.Label(login, text="", fg="red")
label_failed_connection.pack()
label_empty_username = tkinter.Label(signup_frame, text="", fg="red")
label_empty_username.pack()
# Login input
entry_username = tkinter.Entry(input_setup_frame, text=username)
entry_username.bind("<Return>", lambda event, a=None: validate_user(a))
entry_username.pack()
register_username = tkinter.Button(signup_frame, text="Login", command=lambda: validate_user(None))
register_username.pack()

login.protocol("WM_DELETE_WINDOW", check_bad_login)  # Protocol on window exit

login.mainloop()


# Creating the main window
main = tkinter.Tk()
main.title(ui_version)
main.state('zoomed')
# Framing the layout of UI
message_to_send = tkinter.StringVar()
topFrame = tkinter.Frame(main)
topFrame.pack(fill=tkinter.BOTH)
in_out_frame = tkinter.Frame(main)
in_out_frame.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
bottom_frame = tkinter.Frame(in_out_frame)
bottom_frame.pack(side=tkinter.BOTTOM, fill=tkinter.BOTH)
room_frame = tkinter.Frame(in_out_frame)
room_frame.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
images_frame = tkinter.Frame(in_out_frame)
images_frame.pack(side=tkinter.RIGHT)

# Dropdown Menu
menu1 = tkinter.Menu(topFrame)
main.config(menu=menu1)
subMenu1 = tkinter.Menu(menu1, tearoff=0)
menu1.add_cascade(label="Server", menu=subMenu1)
subMenu1.add_command(label="Reconnect to server", command=reconnect_to_server)
subMenu1.entryconfig("Reconnect to server", state="disable")
subMenu1.add_command(label="Exit from server", command=exit_from_ui)

# UI elements
label = tkinter.Label(topFrame, text=ui_version, bg="blue", fg="white")
label.pack(fill=tkinter.X)
labelWelcome = tkinter.Label(topFrame, text="Welcome " + username.get(), bg="blue", fg="white")
labelWelcome.pack(fill=tkinter.X)
label_failed_reconnection = tkinter.Label(topFrame, text="", fg="red")
label_failed_reconnection.pack()

scrollbar = tkinter.Scrollbar(in_out_frame)
# To navigate through past messages.
# Following will contain the messages.
msg_list = tkinter.Listbox(in_out_frame, height=15, width=115, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
msg_list.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)

# Message input
labelUser = tkinter.Label(bottom_frame, text="USER: " + username.get(), width=15, bg="green", fg="white")
labelUser.pack(side=tkinter.LEFT)
scrollbar = tkinter.Scrollbar(bottom_frame)
entry_field = tkinter.Entry(bottom_frame, width=105, textvariable=message_to_send)
entry_field.bind("<Return>", lambda event, a=client.send_messages: send_message(a))
entry_field.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
send_button = tkinter.Button(bottom_frame, text="Send", command=lambda: send_message(client.send_messages))
send_button.pack(side=tkinter.LEFT)
send_image_button = tkinter.Button(bottom_frame, text="Load Image", command=load_image)
send_image_button.pack(side=tkinter.LEFT)

# Room status
current_room = tkinter.StringVar()
current_room.set("")
labelRoom = tkinter.Label(room_frame, text="IN chat room:" + current_room.get(), bg="gray", fg="white")
labelRoom.pack(fill=tkinter.BOTH)
room_users_list = tkinter.Listbox(room_frame, height=30, bg="gray")
room_users_list.pack(fill=tkinter.BOTH)

# Image display (Attempted)
meme_frame = tkinter.Frame(images_frame)
meme_frame.pack(fill="both")
image_list = []

main.protocol("WM_DELETE_WINDOW", exit_from_ui)  # Protocol on window exit
# Run window after login was successful
if bad_login.get() == "Failed":
    main.destroy()
else:
    client_thread = Thread(target=client.run, args=[receive_message])
    client_thread.start()
    send_message(client.send_messages)
    client_room_thread = Thread(target=client.get_client_room_list, args=[])
    client_room_thread.start()

main.mainloop()
