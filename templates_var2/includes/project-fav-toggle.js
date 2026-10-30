<script>
  document.addEventListener("DOMContentLoaded", () => {
    const isFavoritesPage = document.body.dataset.page === "favorites";

    document.querySelectorAll(".project-fav-icon").forEach(button => {
      button.addEventListener("click", async (e) => {
        e.preventDefault();

        const projectId = button.dataset.projectId;
        const isFav = button.dataset.fav === "true";
        const response = await fetch(`/projects/${projectId}/toggle-favorite/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
          },
          body: JSON.stringify({})
        });

        if (!response.ok) {
          alert("Ошибка при обновлении избранного");
          return;
        }
        if (isFavoritesPage && isFav) {
          button.closest(".project-card").remove();
          if (document.querySelectorAll(".project-card").length === 0) {
            const emptyBlock = document.querySelector("#empty-favorite-template");
            if (emptyBlock) emptyBlock.style.display = "block";
          }
          return;
        }
        button.classList.toggle("favorite", !isFav);
        button.classList.toggle("not-favorite", isFav);
        button.dataset.fav = String(!isFav);
      });
    });
  });

  function getCookie(name) {
    if (!document.cookie) return null;
    for (const value of document.cookie.split(";")) {
      const cookie = value.trim();
      if (cookie.startsWith(name + "=")) {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }
    return null;
  }
</script>
