async function fetchConversation(msg, agent_id) {
    let request_data = {agent_id: agent_id}
    if (msg !== null) {
        request_data.msg = msg;
    }
    const response = await fetch('/myconversation', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(request_data)
    });
    
    return await response.json();
}

function createMessageArray(conversation) {
    let messages = [];
    if (conversation.status !== "complete") {
        messages.push({role: 'system', txt: 'There was an error.'});
        return messages;
    }
    
    let conv = conversation.conversation;
    for (let i = 0;i < conv['agent'].length;i++) {
        for (const role of ['agent', 'user']) {
            if (i < conv[role].length) {
                messages.push({role: role, txt: conv[role][i]});
            }
        }
    }

    if (conversation.pending) {
        messages.push({role: 'system', txt: 'Waiting for response'});
    }

    return messages;
}

function updateDisplay(conversation) {
    let conversation_node = document.getElementById("messages");
    conversation_node.innerHTML = '';

    let messages = createMessageArray(conversation);

    for (const msg of messages) {
        let msg_element = document.createElement("div");
        msg_element.setAttribute("class", "msg_" + msg.role);
        msg_element.innerText = msg.txt;
        conversation_node.appendChild(msg_element);
    }
}

async function sendMessage(agent_id) {
    let send_button = document.getElementById("send_button");
    send_button.setAttribute("enabled", "false");
    let input_field = document.getElementById("user_msg");
    let msg = input_field.value;

    try {
        let conversation = await fetchConversation(msg, agent_id);
        updateDisplay(conversation);
        input_field.value = '';
    }
    catch (error) {
        console.error(error.toString());
    }

    send_button.setAttribute("enabled", "true");
}