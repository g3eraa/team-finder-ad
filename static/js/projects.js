// Project-specific JS (complete project action + toggle participate)
(function(){
  document.addEventListener("DOMContentLoaded", function() {
    const completeBtn = document.getElementById("complete-project-btn");
    if (completeBtn) {
      completeBtn.addEventListener("click", function(e) {
        e.preventDefault();
        const projectId = completeBtn.dataset.id;
        if (!projectId) return;
        if (!confirm("Завершить проект? Статус сменится на «Закрыт».")) return;

        fetch(`/projects/${projectId}/complete/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": window.getCookie ? window.getCookie("csrftoken") : "",
            "Content-Type": "application/json"
          },
          body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
          if (data.status === "ok") {
            const statusEl = document.querySelector(".project-status-black");
            if (statusEl) {
              statusEl.textContent = "Закрыт";
              statusEl.classList.add("is-closed");
            }
            completeBtn.remove();
            if (window.toast) window.toast("Проект завершён", { type: 'info' });
          } else {
            if (window.toast) window.toast("Ошибка при завершении проекта", { type: 'error' });
            else alert("Ошибка при завершении проекта");
          }
        })
        .catch(err => {
          console.error("Ошибка запроса:", err);
          if (window.toast) window.toast("Ошибка сети", { type: 'error' });
        });
      });
    }

    const participateBtn = document.getElementById("participate-btn");
    const participantsList = document.getElementById("participants-list");
    const participantsCount = document.getElementById("participants-count");
    if (participateBtn && participantsList && participantsCount) {
      const userId = participateBtn.dataset.userId || null;
      const projectId = participateBtn.dataset.project;
      const userName = participateBtn.dataset.userName || "";
      const userAvatar = participateBtn.dataset.userAvatar || "";

      participateBtn.addEventListener("click", function(e) {
        e.preventDefault();
        if (!projectId) return;

        fetch(`/projects/${projectId}/toggle-participate/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": window.getCookie ? window.getCookie("csrftoken") : "",
            "Content-Type": "application/json"
          },
          body: JSON.stringify({})
        })
        .then(resp => resp.json())
        .then(data => {
          if (data.status !== "ok") {
            if (window.toast) window.toast("Ошибка при изменении участия", { type: 'error' });
            else alert("Ошибка при изменении участия");
            return;
          }

          if (data.participant) {
            participateBtn.textContent = "Отказаться от участия";

            const noParticipants = document.getElementById("no-participants");
            if (noParticipants) noParticipants.remove();

            const a = document.createElement("a");
            a.href = `/users/${userId}`;
            a.id = `participant-${userId}`;

            const item = document.createElement("div");
            item.className = "participant-item";
            const img = document.createElement("img");
            img.src = userAvatar;
            img.alt = "Аватар";
            img.className = "participant-avatar";
            const info = document.createElement("div");
            info.className = "participant-info";
            const name = document.createElement("span");
            name.className = "participant-name";
            name.textContent = userName;
            const role = document.createElement("span");
            role.className = "participant-role";
            role.textContent = "Участник";

            info.append(name, role);
            item.append(img, info);
            a.appendChild(item);
            participantsList.appendChild(a);

            participantsCount.textContent = parseInt(participantsCount.textContent) + 1;

          } else {
            participateBtn.textContent = "Участвовать";

            const el = document.getElementById(`participant-${userId}`);
            if (el) el.remove();

            const newCount = parseInt(participantsCount.textContent) - 1;
            participantsCount.textContent = newCount;

            if (newCount === 0) {
              const p = document.createElement("p");
              p.id = "no-participants";
              p.textContent = "Пока нет участников";
              participantsList.appendChild(p);
            }
          }
        })
        .catch(err => {
          console.error("Ошибка запроса:", err);
          if (window.toast) window.toast("Ошибка сети", { type: 'error' });
        });
      });
    }
  });
})();
