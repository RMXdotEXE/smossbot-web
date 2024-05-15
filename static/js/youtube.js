/* 
 * ==============================================
 * IFrame API setup
 * ==============================================
 */

var player;
var currVideoTimeoutID;
var currVideoVars = {};
var video_id_queue = [];
var tag = document.createElement('script');
tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
document.getElementById('player').style = "visibility: hidden;";

function onYouTubeIframeAPIReady()
{
    var params = {
        width: "1280",
        height: "720",
        playerVars: { 'playsinline': 1 },
        events: {
            'onReady': function(event) { console.log("YT player ready!") },
            'onStateChange': function (event)
            {
                if (event.data == YT.PlayerState.PLAYING)
                    { currVideoTimeoutID = setTimeout(loadNextVideoOrQuit, currVideoVars.vars.maxsecs * 1000); }
                else
                    { clearTimeout(currVideoTimeoutID); }

                if (event.data == YT.PlayerState.ENDED)
                    { loadNextVideoOrQuit(); }
            },
            'onError': function(event)
            {
                console.log("Error occured playing YT video. Error code " + event.data);

                packet = {
                    'username': username,
                    'errored': true,
                    'redemption_data': currVideoVars.redemption_data,
                    'error_data': {
                        'code': event.data,
                        'status': "Error occured playing YT video (" + event.data + ")."
                    }
                }
                botSocket.send(JSON.stringify(packet));

                loadNextVideoOrQuit();
            }
        }
    }
    player = new YT.Player('player', params);
}

function addVideoToQueue(youtube_id, incoming_data)
{
    queue_data = {
        'id': youtube_id,
        'redemption_data': incoming_data.redemption_data,
        'vars': incoming_data.vars
    };

    video_id_queue.push(queue_data);
    console.log("Added " + youtube_id + " to the queue.");

    // If video player isn't playing anything, just load this and play it.
    if (player.getPlayerState() != YT.PlayerState.PLAYING)
    {
        currVideoVars = video_id_queue.shift();
        document.getElementById('player').style = "visibility: visible;";
        player.loadVideoById(currVideoVars.id);
        if (queue_data.vars.mutespotify)
        {
            packet = {
                'username': username,
                'spotify_control': "pausemusic"
            }
            botSocket.send(JSON.stringify(packet));
        }
        console.log("Playing YT video off empty queue.");
    }
}

function loadNextVideoOrQuit()
{
    // Player ended and there's still a video in queue, so play that
    if (video_id_queue.length > 0)
    {
        currVideoVars = video_id_queue.shift();
        player.loadVideoById(currVideoVars.id);
        console.log("Playing YT video off queue.");
    }
    else
    {
        // All done!
        document.getElementById('player').style = "visibility: hidden;";
        if (currVideoVars.vars.mutespotify)
        {
            packet = {
                'username': username,
                'spotify_control': "playmusic"
            }
            botSocket.send(JSON.stringify(packet));
        }
        console.log("Finished the queue.");
        player.stopVideo();
    }
}