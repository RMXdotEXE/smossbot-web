/* 
 * ==============================================
 * Sound redemptions
 * ==============================================
 */

function getSound(incoming_data)
{
    let filepath = "";

    $.ajax({
        url: fileAPIURL,
        data: {
            'user_hash': username, 
            'tag': incoming_data.redemption_data.input
        },
        success: function(response)
        {
            if (!response.exists)
            {
                packet = {
                    'username': username,
                    'errored': true,
                    'redemption_data': incoming_data.redemption_data,
                    'error_data': {
                        'code': 404,
                        'status': response.errormsg
                    }
                };
                
                botSocket.send(JSON.stringify(packet));

                console.log("tag doesnt exist?");
                
                return;
            }

            filepath = response.filename;
            playSound(filepath);
        },
        error: function(jqXHR, textStatus, errorThrown)
        {
            console.log(jqXHR);
            console.log(textStatus);
            console.log(errorThrown);
        }
    });
}

function playSound(filepath)
{
    console.log("Playing sound: " + filepath);
    audio.src = mediaDir + filepath;
    audio.play();
}