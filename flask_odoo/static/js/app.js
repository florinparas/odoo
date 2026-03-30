// ─── Flask-Odoo Client-side JS ──────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss flash messages after 4s
    document.querySelectorAll('.alert-dismissible').forEach(function (el) {
        setTimeout(function () {
            var btn = el.querySelector('.btn-close');
            if (btn) btn.click();
        }, 4000);
    });

    // Clickable table rows
    document.querySelectorAll('.o-list-view tbody tr[data-href]').forEach(function (row) {
        row.addEventListener('click', function (e) {
            if (e.target.closest('a, button, form')) return;
            window.location = this.dataset.href;
        });
    });

    // Order lines: add/remove
    var lineContainer = document.getElementById('order-lines');
    var addLineBtn = document.getElementById('add-line');
    if (addLineBtn && lineContainer) {
        var lineIdx = lineContainer.querySelectorAll('.order-line').length;

        addLineBtn.addEventListener('click', function () {
            var tpl = document.getElementById('line-template').innerHTML;
            tpl = tpl.replace(/__IDX__/g, lineIdx);
            var div = document.createElement('div');
            div.className = 'order-line row g-2 mb-2 align-items-end';
            div.innerHTML = tpl;
            lineContainer.appendChild(div);
            lineIdx++;
        });

        lineContainer.addEventListener('click', function (e) {
            if (e.target.closest('.remove-line')) {
                e.target.closest('.order-line').remove();
            }
        });

        // Auto-fill price when product selected
        lineContainer.addEventListener('change', function (e) {
            if (e.target.classList.contains('product-select')) {
                var option = e.target.selectedOptions[0];
                var price = option ? option.dataset.price : '';
                var row = e.target.closest('.order-line');
                var priceInput = row.querySelector('.line-price');
                if (priceInput && price) priceInput.value = price;
            }
        });
    }
});
