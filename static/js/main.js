function Dropdown(element, optionSelectCallback=null)
{
    this.dropdown = element;
    this.placeholder = this.dropdown.children('.placeholder');
    this.options = this.dropdown.find('ul.dropdown .dropdown-li-container');
    this.originalOptions = this.dropdown.find('ul.dropdown .dropdown-li-container');
    this.val = '';
    this.selectedID = null;
    this.optionSelectCallback = optionSelectCallback;
    this.initEvents();

    let preSelected = this.options.find("[selected]");
    if (preSelected.length == 1)
    {
        this.setOption(preSelected.attr("id"), preSelected.text());
    }
}

Dropdown.prototype =
{
    initEvents: function()
    {
        let ddObj = this;

        ddObj.dropdown.on('click', function(event)
        {
            // TODO: Would be nice
            // $(".dropdown-container").removeClass('active');
            $(this).toggleClass('active');
            event.stopPropagation();
        });

        ddObj.options.on('click', {ddObj: ddObj}, this.selectOption);
    },
    addOption: function(id, display)
    {
        // TODO: Clean this mess up.
        // Checks to see if ID already exists in this.options.
        let exists = false;
        $(this.options).each(function()
        {
            if (id == this.id )
                { exists = true; }
        });
        if (exists) { return; }

        // Construct the new option and add it to dropdown
        let newOption = '<li id="' + id + '">' + display + '</li>';
        let newOptionContainer = $('<div class="dropdown-li-container">' + newOption + '</div>');
        this.options = this.options.add(newOptionContainer);
        this.dropdown.children('.dropdown').append(newOptionContainer);
        $(newOptionContainer).on('click', {ddObj: this}, this.selectOption);
    },
    setOption: function(id, label)
    {
        this.val = label;
        this.placeholder.text(this.val);
        this.selectedID = id;
    },
    selectOption: function(event)
    {
        let option = $(this).children("li");
        let ddObj = event.data.ddObj;
        ddObj.val = option.text();
        ddObj.placeholder.text(ddObj.val);
        ddObj.selectedID = option.attr("id");
        ddObj.optionSelectCallback ? ddObj.optionSelectCallback() : null;
    },
    restore: function()
    {
        let ddObj = this;

        ddObj.dropdown.children('.dropdown').empty();
        this.originalOptions.each(function(index, option)
        {
            ddObj.dropdown.children('.dropdown').append(option);
            $(option).on('click', {ddObj: ddObj}, ddObj.selectOption);
        });
    },
    getParsedID: function(delimiter="-")
    {
        if (!this.selectedID)
            { return null; }
        return this.selectedID.substring(this.selectedID.lastIndexOf(delimiter) + 1);
    },
    getText: function() { return this.val; },
    getID: function() { return this.selectedID; },
    
}

$(document).click(function()
{
    $(".dropdown-container").removeClass('active');
});





function Modal(modal, openBtn, closeBtn)
{
    this.modal = modal;
    this.openBtn = openBtn;
    this.closeBtn = closeBtn;
    this.isOpened = false;

    this.initEvents();
}

Modal.prototype = 
{
    initEvents: function()
    {
        let modal = this;

        this.openBtn.on("click", {modalObj: modal}, this.fadeIn);
        this.closeBtn.on("click", {modalObj: modal}, this.fadeOut);

        /* TODO: fix. should close modal on click outside the modal. problem is
         * that the modal content doesnt stretch across the entire screen.
         * $(window).on("click", function(event)
         * {
         *     if ($(event.target).is(modal.modal)) { modal.manualFadeOut(); }
         * });
         */
    },
    fadeIn: function(event)
    {
        $("#dimBackground").fadeIn(200);
        event.data.modalObj.modal.css("display", "block");
        event.data.modalObj.isOpened = true;
    },
    fadeOut: function(event)
    {
        $("#dimBackground").fadeOut(200);
        event.data.modalObj.modal.css("display", "none");
        event.data.modalObj.isOpened = false;
    },
    manualFadeOut: function()
    {
        $("#dimBackground").fadeOut(200);
        this.modal.css("display", "none");
        this.isOpened = false;
    },
    prefillModal: function(codeData)
    {
        for (const[key, value] of Object.entries(codeData))
        {
            // Set checked property incase incoming value is a boolean
            if (typeof value === "boolean")
            {
                $("#" + key).prop("checked", value);
                $("#" + key).prop("disabled", value); // If required text is true, then ensure it doesn't change
            }

            // Default: use $.val()
            $("#" + key).val(value);
        }
    }
}