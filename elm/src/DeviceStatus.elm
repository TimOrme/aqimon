module DeviceStatus exposing (..)

import Bootstrap.Grid as Grid
import Bootstrap.Grid.Col as Col
import Bootstrap.Grid.Row as Row
import Html exposing (Attribute, Html, div, h1, h5, img, text)
import Html.Attributes exposing (alt, class, src, style)


type DeviceState
    = Reading
    | Idle
    | Failing


type alias DeviceInfo =
    { state : DeviceState
    , lastException : Maybe String
    }


getDeviceInfo : DeviceInfo -> Html msg
getDeviceInfo deviceInfo =
    Grid.container []
        [ Grid.row [ Row.attrs [ class "align-items-center" ] ]
            [ Grid.col [ Col.attrs [ style "max-width" "64px", style "margin-right" "1em" ] ] [ img [ src (deviceStatusImage deviceInfo.state) ] [] ]
            , Grid.col []
                [ Grid.row []
                    [ Grid.col []
                        [ h5 [ style "color" (deviceStatusColor deviceInfo.state) ] [ text (deviceStatusToString deviceInfo.state) ] ]
                    ]
                , Grid.row []
                    [ Grid.col [] [ text (deviceInfo.lastException |> Maybe.withDefault "") ] ]
                ]
            ]
        ]


deviceStatusImage : DeviceState -> String
deviceStatusImage deviceStatus =
    case deviceStatus of
        Reading ->
            "/static/images/loading.gif"

        Idle ->
            "/static/images/idle.png"

        Failing ->
            "/static/images/failing.png"


deviceStatusColor : DeviceState -> String
deviceStatusColor deviceStatus =
    case deviceStatus of
        Reading ->
            "green"

        Idle ->
            "gray"

        Failing ->
            "red"


deviceStatusToString : DeviceState -> String
deviceStatusToString deviceStatus =
    case deviceStatus of
        Reading ->
            "Reading"

        Idle ->
            "Idle"

        Failing ->
            "Failing"
