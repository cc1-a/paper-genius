
document.addEventListener("DOMContentLoaded", function () {

    /* =======================
       YEAR VALIDATION LOGIC
       ======================= */
    const forms = document.querySelectorAll(".form_shop");

forms.forEach(form => {
    // Assuming these IDs correctly point to your "From" and "To" year/date selectors
    const fromSelect = form.querySelector("#selected_year_from");
    const toSelect = form.querySelector("#selected_year_to");

    fromSelect.addEventListener("change", () => {
        const fromValue = fromSelect.value;

        // Clear the To selection
        toSelect.value = "";

        // Enable/disable options
        Array.from(toSelect.options).forEach(option => {
            if (!option.value) return; // skip empty placeholder
            
            // **CORRECTION HERE: Use <= to disable the current "From" year as well.**
            option.disabled = option.value <= fromValue; 
        });
    });
});



    /* =======================
       CART SUMMARY LOGIC
       ======================= */
    const checkboxes = document.querySelectorAll(".item-checkbox");
    const countDisplay = document.querySelector("#cart-selected-count");
    const checkoutButtonCount = document.querySelector("#checkout-button-count");
    const totalDisplay = document.querySelector("#cart-total-price");

    function updateCartSummary() {
        let selectedCount = 0;
        let totalPrice = 0;

        checkboxes.forEach(checkbox => {
            if (checkbox.checked) {
                const itemContainer = checkbox.closest(".container-cart");
                const price = parseFloat(itemContainer.getAttribute("data-price"));

                if (!isNaN(price)) {
                    selectedCount++;
                    totalPrice += price;
                }
            }
        });

        if (countDisplay) countDisplay.textContent = selectedCount;
        if (checkoutButtonCount) checkoutButtonCount.textContent = selectedCount;
        if (totalDisplay) totalDisplay.textContent = "R" + totalPrice.toFixed(2);
    }

    // Attach events
    checkboxes.forEach(cb => cb.addEventListener("change", updateCartSummary));

    // Initial update
    updateCartSummary();
});

