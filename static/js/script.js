document.addEventListener("DOMContentLoaded", function () {

    console.log("Food Express Restaurant Ordering System Loaded");


    // Confirm before deleting a food item

    const deleteButtons =
        document.querySelectorAll(".delete-btn");

    deleteButtons.forEach(function (button) {

        button.addEventListener("click", function (event) {

            const confirmation =
                confirm("Are you sure you want to delete this item?");

            if (!confirmation) {

                event.preventDefault();

            }

        });

    });

});