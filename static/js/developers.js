const names = document.querySelectorAll("#devs li")
names.forEach(element => {
    element.addEventListener("click", function () {
        let name = element.getAttribute("developer_name");
        console.log("Hello bro: ", name)
    });
});
