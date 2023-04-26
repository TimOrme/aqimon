module DeviceStatus exposing (..)

import Bootstrap.Grid as Grid
import Bootstrap.Grid.Col as Col
import Bootstrap.Grid.Row as Row
import Html exposing (Attribute, Html, div, h1, h5, img, text)
import Html.Attributes exposing (alt, class, src, style)
import Maybe
import Time exposing (..)


{-| Possible device states
-}
type DeviceState
    = Reading
    | WarmingUp
    | Idle
    | Failing


{-| Model for device info widget
-}
type alias DeviceInfo =
    { state : DeviceState
    , lastException : Maybe String
    , currentTime : Maybe Posix
    , nextSchedule : Maybe Posix
    }


{-| HTML widget for displaying the device status.

Includes general status, time to next read, and exception info if applicable.

-}
getDeviceInfo : DeviceInfo -> Html msg
getDeviceInfo deviceInfo =
    Grid.container []
        [ Grid.row [ Row.attrs [] ]
            [ Grid.col [ Col.attrs [ class "text-center", style "padding" "2em" ] ] [ img [ src (deviceStatusImage deviceInfo.state) ] [] ] ]
        , Grid.row []
            [ Grid.col [ Col.attrs [ style "text-align" "center" ] ] [ h5 [ style "color" (deviceStatusColor deviceInfo.state) ] [ text (deviceStatusToString deviceInfo.state) ] ] ]
        , Grid.row []
            [ Grid.col [ Col.attrs [ style "text-align" "center" ] ] [ text (deviceInfo.lastException |> Maybe.withDefault "") ] ]
        , htmlIf
            (Grid.row []
                [ Grid.col [ Col.attrs [ style "text-align" "center" ] ]
                    [ text ("Next read in: " ++ (Maybe.map2 formatDuration deviceInfo.currentTime deviceInfo.nextSchedule |> Maybe.withDefault "")) ]
                ]
            )
            (shouldShowTimer deviceInfo.state)
        ]


{-| Get the image icon for the device status box
-}
deviceStatusImage : DeviceState -> String
deviceStatusImage deviceStatus =
    case deviceStatus of
        Reading ->
            "/static/images/loading.gif"

        WarmingUp ->
            "/static/images/warmingup.gif"

        Idle ->
            "/static/images/idle.png"

        Failing ->
            "/static/images/failing.png"


{-| Get the color of the device status box
-}
deviceStatusColor : DeviceState -> String
deviceStatusColor deviceStatus =
    case deviceStatus of
        Reading ->
            "green"

        WarmingUp ->
            "orange"

        Idle ->
            "gray"

        Failing ->
            "red"


{-| Convert the device status to a readable string.
-}
deviceStatusToString : DeviceState -> String
deviceStatusToString deviceStatus =
    case deviceStatus of
        Reading ->
            "Reading"

        WarmingUp ->
            "Warming Up"

        Idle ->
            "Idle"

        Failing ->
            "Failing"


{-| Determine if we should show the countdown timer.
-}
shouldShowTimer : DeviceState -> Bool
shouldShowTimer deviceState =
    deviceState == Idle || deviceState == Failing


{-| Conditionally display some block of HTML
-}
htmlIf : Html msg -> Bool -> Html msg
htmlIf el cond =
    if cond then
        el

    else
        text ""


{-| Format a unix timestamp as a string like MM/DD HH:MM:SS
-}
formatDuration : Posix -> Posix -> String
formatDuration currentTime scheduledTime =
    let
        durationMillis =
            posixToMillis scheduledTime - posixToMillis currentTime

        hour =
            durationMillis // 1000 // 60 // 60

        minute =
            modBy 60 (durationMillis // 1000 // 60)

        second =
            modBy 60 (durationMillis // 1000)
    in
    if durationMillis > 0 then
        String.padLeft 2 '0' (String.fromInt hour) ++ ":" ++ String.padLeft 2 '0' (String.fromInt minute) ++ ":" ++ String.padLeft 2 '0' (String.fromInt second)

    else
        "00:00:00"
