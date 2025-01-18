function get_agent_from_url() {
    const urlParams = new URLSearchParams(window.location.search);

    return urlParams.get('agent');
}

const agent_id = get_agent_from_url();

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
            if (!(role in conv)) {
                continue;
            }
            if (i < conv[role].length) {
                messages.push({role: role, txt: conv[role][i]});
            }
        }
    }

    if (conversation.pending) {
        messages.push({role: 'system', txt: "Waiting for response. This may take a few minutes. You can close this page and check back later if you don't have time to wait."});
    }

    return messages;
}

function updateDisplay(conversation) {
    let conversation_node = document.getElementById("messages");
    let send_button = document.getElementById("send_button");

    if (conversation.pending) {
        send_button.disabled = true;
    } else {
        send_button.disabled = false;
    }

    conversation_node.innerHTML = '';

    let messages = createMessageArray(conversation);

    for (const msg of messages) {
        let msg_element = document.createElement("div");
        msg_element.setAttribute("class", "msg_" + msg.role);
        msg_element.innerText = msg.txt;
        conversation_node.appendChild(msg_element);
    }
}

async function load_page(agent_id) {
    try {
        let conversation = await fetchConversation(null, agent_id);
        updateDisplay(conversation);
    }
    catch (error) {
        console.error(error.toString());
    }
}

function page_loader() {
    load_page(agent_id);
    const pollInterval = setInterval(() => {
        load_page(agent_id)
    }, 15000); // Poll every 5 seconds
}

async function sendMessage() {
    let send_button = document.getElementById("send_button");
    send_button.disabled = true;
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
}