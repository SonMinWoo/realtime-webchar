const messageList = document.querySelector(".chattings");
const nickForm = document.querySelector("#nickname");
const messageForm = document.querySelector("#message");
const chatbox = document.querySelector(".chatbox");
const socket = new WebSocket(`ws://${window.location.host}/chat`)

let userList = document.querySelector(".userlist");
let nownick = "";

function makeMessage(action, payload) {
    console.log(document.cookie.split(";")[0])
    let msg = {};
    if (action === "new_message") {
        msg = {"action": action, "message" : payload};
    } else if (action === "nick") {
        msg = {"action": "set_nickname", "nick" : payload};
    } else if (action === "new_connect") {
        msg = {"action": "user_list", "cookie": payload};
    } else {
        msg = {"action": action};
    }
    return JSON.stringify(msg);
}

socket.addEventListener("open", () => {
    console.log("Connected to Server O");
});

socket.addEventListener("message", (message) => {
    const li = document.createElement("li");
    getjson = JSON.parse(message.data)

    switch (getjson['action']) {
        case "join":
            li.innerText = `${getjson['user']} is joined! `;
            const user = document.createElement("li");
            user.innerText = `${getjson['user']}`;
            userList.append(user);
            break;
        case 'new_message':
            if (nownick === getjson['user']) {
                li.style.color = 'blue';
            } 
            li.innerText = `${getjson['user']} : ${getjson['message']}`;
            break;
        case 'left':
            li.innerText = `${getjson['user']} left this room.`;
            socket.send(makeMessage("user_list", ""));
            break;
        case 'change_nick':
            li.innerText = `${getjson['from_user']} is changed nickname to ${getjson['to_user']}`;
            socket.send(makeMessage("user_list", ""));
            break;
        case 'connecting':
            socket.send(makeMessage("new_connect", document.cookie.split(";")[0].split("=")[0]));
            nownick = getjson['user'];
            document.cookie=`cookie${nownick.slice(4)}=value`;
            return;
        case 'user_list':
            userList.innerHTML = ""
            for (nick in getjson['users']){
                const li = document.createElement("li");
                li.innerText = getjson['users'][nick];
                userList.append(li);
            } 
            return;
        case 'set_nick':
            if(getjson['success']) {
                socket.send(makeMessage("user_list", ""));
            } else {
                alert("duplicate nickname is not allowed!");
            }
            return;
        default:
            console.log("unknown action")
    }
    messageList.append(li);
    chatbox.scrollTop = chatbox.scrollHeight;
});

socket.addEventListener("close", () => {
    console.log("Disconnected to Server X");
});

function handleSubmit(event) {
    event.preventDefault();
    const input = messageForm.querySelector("input");
    socket.send(makeMessage("new_message", input.value));
    input.value = "";
}

function handleNickSubmit(event) {
    event.preventDefault();
    const input = nickForm.querySelector("input");
    socket.send(makeMessage("nick", input.value));
    input.value = "";
}

messageForm.addEventListener("submit", handleSubmit);
nickForm.addEventListener("submit", handleNickSubmit);