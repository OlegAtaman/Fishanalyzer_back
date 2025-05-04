document.addEventListener("DOMContentLoaded", () => {
  const forwardSwitch = document.getElementById("forwardToSecuritySwitch");
  const emailField = document.getElementById("securityEmail");
  const formBlock = document.getElementById("add-rule-form");
  const showFormBtn = document.getElementById("show-rule-form-btn");



  document.querySelectorAll('.delete-rule-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const id = this.dataset.id;
      if (confirm("Ви впевнені, що хочете видалити це правило?")) {
        axios({
          method: 'delete',
          url: '/settings/',
          data: { id: id }
        }).then(() => {
          this.closest("tr").remove();
        });
      }
    });
  });

  forwardSwitch.addEventListener("change", () => {
    emailField.disabled = !forwardSwitch.checked;
  });

  showFormBtn.addEventListener("click", () => {
    formBlock.style.display = "block";
    console.log('hii');
  });

  document.getElementById("add-rule-form").addEventListener("submit", function (e) {
    e.preventDefault();
  
    const recipientInput = document.getElementById("recipientInput").value;
    const senderInput = document.getElementById("senderInput").value;
  
    const recipients = recipientInput.split(";").map(s => s.trim()).filter(s => s);
    const senders = senderInput.split(";").map(s => s.trim()).filter(s => s);
  
    // Валідація
    const invalidRecipients = recipients.filter(r => !isValidEmailEntry(r));
    const invalidSenders = senders.filter(s => !isValidEmailEntry(s));
  
    if (invalidRecipients.length > 0 || invalidSenders.length > 0) {
      alert("Невірний формат email/домена:\n" +
        (invalidRecipients.length ? "Отримувачі: " + invalidRecipients.join(", ") + "\n" : "") +
        (invalidSenders.length ? "Відправники: " + invalidSenders.join(", ") : "")
      );
      return;
    }
  
    const data = {
      recipient: recipientInput,
      sender: senderInput,
      action: document.getElementById("actionSelect").value,
      priority: parseInt(document.getElementById("priorityInput").value),
    };
  
    axios.post("/settings/", data).then(response => {
      renderRule(response.data);
      sortRulesTable();
      e.target.reset();
      e.target.style.display = "none";
    });
  });

  function sortRulesTable() {
    const table = document.querySelector("#rules-table tbody");
    const rows = Array.from(table.rows).filter((row) => !row.dataset.default);
    rows.sort((a, b) => parseInt(a.cells[3].textContent) - parseInt(b.cells[3].textContent));
    rows.forEach((row) => table.insertBefore(row, table.querySelector("tr[data-default='true']")));
  }

  function createDeleteButton(id) {
    const td = document.createElement("td");
    td.style.textAlign = "right";
    td.style.width = "40px";
    td.style.verticalAlign = "middle";
  
    const btn = document.createElement("button");
    btn.className = "btn p-0 m-0";
    btn.title = "Видалити";
  
    btn.onclick = function () {
      if (confirm("Ви впевнені, що хочете видалити це правило?")) {
        axios({
          method: 'delete',
          url: '/settings/',
          data: { id: id }
        }).then(() => {
          this.closest("tr").remove();
        });
      }
    };
  
    const img = document.createElement("img");
    img.src = "/static/images/del.png";
    img.alt = "✖";
    img.style.width = "20px";
    img.style.height = "20px";
    img.style.margin = "5px";
  
    btn.appendChild(img);
    td.appendChild(btn);
    return td;
  }
  

  function renderRule(rule) {
    const table = document.querySelector("#rules-table tbody");

    const badgeClass = {
      allow: "bg-success",
      check: "bg-warning text-dark",
      drop: "bg-danger",
    }[rule.action];

    const badgeText = rule.action.toUpperCase();

    const newRow = document.createElement("tr");
    newRow.classList.add("rule-row");
    newRow.innerHTML = `
      <td>${rule.recipient}</td>
      <td>${rule.sender}</td>
      <td><span class="badge ${badgeClass}">${badgeText}</span></td>
      <td>${rule.priority}</td>
    `;
    if (rule.priority !== 10000) newRow.appendChild(createDeleteButton(rule.id));
    table.appendChild(newRow);
  }

  axios.get("/settings/").then(response => {
    response.data.forEach(renderRule);
    sortRulesTable();
  });

  document.querySelector(".card-body form").addEventListener("submit", function (e) {
    e.preventDefault();
  
    const data = {
      save_drop: document.getElementById("storeDroppedSwitch").checked,
      redirect_to_sec: document.getElementById("forwardToSecuritySwitch").checked,
      sec_email: document.getElementById("securityEmail").value,
    };
  
    axios.put("/settings/", data)
      .then(() => alert("Налаштування збережено!"))
      .catch(() => alert("Помилка при збереженні!"));
  });

  function isValidEmailEntry(entry) {
    entry = entry.trim();
    return (
      entry === '*' ||                                     // Усі
      /^\*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(entry) ||   // Домен
      /^\*\.[a-zA-Z]{2,}$/.test(entry) ||                  // Регіон (наприклад, *.ru)
      /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(entry) // Повна email адреса
    );
  }
});


