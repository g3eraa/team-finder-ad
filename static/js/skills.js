// Profile skills UI logic
(function(){
  document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("skills-container");
    if (!container) return;

    const projectId = container.dataset.projectId;
    const userId = container.dataset.userId;

    let skillsUrl, addUrl, removeUrl;
    if (userId) {
      skillsUrl = `/users/skills/`;
      addUrl = `/users/${userId}/skills/add/`;
      removeUrl = (skillId) => `/users/${userId}/skills/${skillId}/remove/`;
    } else {
      skillsUrl = `/projects/skills/`;
      addUrl = `/projects/${projectId}/skills/add/`;
      removeUrl = (skillId) => `/projects/${projectId}/skills/${skillId}/remove/`;
    }

    const addBtn = document.getElementById("add-skill-btn");
    const inputWrapper = document.getElementById("skill-input-wrapper");
    const input = document.getElementById("skill-input");
    const suggestions = document.getElementById("skill-suggestions");

    if (!addBtn || !inputWrapper || !input || !suggestions) return;

    addBtn.addEventListener("click", () => {
      addBtn.classList.add("hidden");
      inputWrapper.classList.remove("hidden");
      input.value = "";
      suggestions.innerHTML = "";
      suggestions.classList.add("hidden");
      input.focus();
    });

    let t = null;
    input.addEventListener("input", () => {
      const q = input.value.trim();
      clearTimeout(t);
      if (!q) {
        suggestions.classList.add("hidden");
        suggestions.innerHTML = "";
        return;
      }
      t = setTimeout(async () => {
        const res = await fetch(`${skillsUrl}?q=${encodeURIComponent(q)}`);
        if (!res.ok) return;
        const data = await res.json();

        suggestions.innerHTML = "";
        data.forEach(s => {
          const li = document.createElement("li");
          li.textContent = s.name;
          li.dataset.id = s.id;
          li.className = "suggestion-item";
          suggestions.appendChild(li);
        });

        const exact = data.some(s => s.name.toLowerCase() === q.toLowerCase());
        if (!exact) {
          const liNew = document.createElement("li");
          liNew.textContent = `Создать «${q}»`;
          liNew.dataset.name = q;
          liNew.className = "create-new";
          suggestions.appendChild(liNew);
        }

        suggestions.classList.remove("hidden");
      }, 200);
    });

    suggestions.addEventListener("mousedown", async (e) => {
      const li = e.target.closest("li");
      if (!li) return;

      if (li.classList.contains("create-new")) {
        await addSkillByName(li.dataset.name);
      } else if (li.dataset.id) {
        await addSkillById(li.dataset.id);
      }
      hideInput();
    });

    function moveActive(step) {
      const items = [...suggestions.querySelectorAll("li")];
      if (!items.length || suggestions.classList.contains("hidden")) return;
      const current = items.findIndex(li => li.classList.contains("active"));
      const next = (current + step + items.length) % items.length;
      items.forEach(li => li.classList.remove("active"));
      items[next].classList.add("active");
      items[next].scrollIntoView({ block: "nearest" });
    }

    input.addEventListener("keydown", async (e) => {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        moveActive(e.key === "ArrowDown" ? 1 : -1);
      }
      if (e.key === "Enter") {
        e.preventDefault();
        const q = input.value.trim();
        if (!q) return;

        // Подсказку берём, только если её выбрали стрелками; иначе — ровно то, что введено.
        const active = suggestions.querySelector("li.active");
        if (active && active.dataset.id) {
          await addSkillById(active.dataset.id);
        } else {
          await addSkillByName(active ? active.dataset.name : q);
        }
        hideInput();
      }
      if (e.key === "Escape") {
        hideInput();
      }
    });

    input.addEventListener("blur", () => setTimeout(hideInput, 120));

    function hideInput() {
      inputWrapper.classList.add("hidden");
      suggestions.classList.add("hidden");
      addBtn.classList.remove("hidden");
    }

    container.addEventListener("click", async (e) => {
      if (e.target.classList.contains("remove-skill-btn")) {
        const chip = e.target.closest(".skill-chip");
        const skillId = chip.dataset.id;
        const res = await fetch(removeUrl(skillId), {
          method: "POST",
          headers: { "X-CSRFToken": getCookie("csrftoken") }
        });
        if (res.ok) {
          chip.remove();
        } else {
          showError(res);
        }
      }
    });

    async function showError(res) {
      let message = "Не удалось сохранить навык. Попробуйте ещё раз.";
      try {
        const data = await res.json();
        if (data.message) message = data.message;
      } catch (err) {
        // ответ не JSON — оставляем общее сообщение
      }
      if (window.toast) window.toast(message, { type: "error" });
      else alert(message);
    }

    async function addSkillById(skillId) {
      const res = await fetch(addUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ skill_id: skillId }),
      });
      if (res.ok) {
        const skill = await res.json();
        appendChip(skill.id, skill.name);
      } else {
        showError(res);
      }
    }

    async function addSkillByName(name) {
      const res = await fetch(addUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ name }),
      });
      if (res.ok) {
        const skill = await res.json();
        appendChip(skill.id, skill.name);
      } else {
        showError(res);
      }
    }

    function appendChip(id, name) {
      if (container.querySelector(`.skill-chip[data-id="${id}"]`)) return;

      const chip = document.createElement("span");
      chip.className = "skill-chip";
      chip.dataset.id = id;
      // Название навыка задают пользователи, поэтому только textContent, без innerHTML.
      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "remove-skill-btn";
      removeBtn.textContent = "×";
      removeBtn.setAttribute("aria-label", `Удалить навык ${name}`);
      removeBtn.title = "Удалить";
      chip.append(document.createTextNode(`${name} `), removeBtn);

      container.insertBefore(chip, addBtn);

      const empty = container.querySelector(".skill-empty");
      if (empty) empty.remove();
    }

    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
          cookie = cookie.trim();
          if (cookie.startsWith(name + "=")) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
  });
})();
