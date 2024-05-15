class Validators
{
    static forceStrLength(input, min, max)
    {
        input.on("change", function()
        {
            let val = $(this).val();
            if (val.length < min || val.length > max)
            {
                this.setCustomValidity("Length must be within range [" + min + ", " + max + "].");
            }
            else
            {
                this.setCustomValidity("");
            }
        });
    }

    static forceInt(input)
    {
        input.on("change", function()
        {
            let val = $(this).val();
            if (val.indexOf(".") !== -1 || !Number.isInteger(+val))
            {
                this.setCustomValidity("Must be an integer.");
            }
            else
            {
                this.setCustomValidity("");
            }
        });
    }

    static forceIntInRange(input, min, max=2147483647)
    {
        input.on("change", function()
        {
            let val = $(this).val();
            if (val.indexOf(".") !== -1 || !Number.isInteger(+val))
            {
                this.setCustomValidity("Must be an integer.");
            }
            else if (+val < min || +val > max)
            {
                this.setCustomValidity("Must be within range [" + min + ", " + max + "].");
            }
            else
            {
                this.setCustomValidity("");
            }
        });
    }
}