function sendOrder(){
  const name = orderName.value.trim();
  const phone = orderPhone.value.trim();
  const service = orderService.value;
  const note = orderNote.value.trim();

  if(!name || !phone || !service){
    orderStatus.innerText = "Vyplňte jméno, telefon a službu.";
    return;
  }

  const message =
`Poptávka – VV Detailing

Jméno: ${name}
Telefon: ${phone}
Služba: ${service}
Poznámka: ${note || "-"}`;

  window.open(
    "https://wa.me/420606573774?text=" +
    encodeURIComponent(message),
    "_blank"
  );

  orderStatus.innerText = "Otevírám WhatsApp…";
}
/* ===== SCROLL REVEAL ===== */
const reveals = document.querySelectorAll(".reveal");

const observer = new IntersectionObserver(
  entries => {
    entries.forEach(e=>{
      if(e.isIntersecting){
        e.target.classList.add("show");
        observer.unobserve(e.target);
      }
    });
  },
  { threshold:0.15 }
);

reveals.forEach(el=>observer.observe(el));
