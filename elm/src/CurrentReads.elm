module CurrentReads exposing (..)

import Bootstrap.Grid as Grid
import Bootstrap.Grid.Col as Col
import Bootstrap.Grid.Row as Row
import EpaCommon exposing (EpaLevel, getColorForLevel)
import Html exposing (Attribute, Html, a, div, h1, h5, img, text)
import Html.Attributes exposing (alt, class, href, src, style)
import Maybe
import Time exposing (..)


{-| Model for device info widget
-}
type alias CurrentReads =
    { epaLevel : Maybe EpaLevel
    , lastEpaRead : Maybe Float
    , lastPm10 : Maybe Float
    , lastPm25 : Maybe Float
    }


{-| HTML widget for displaying the device status.

Includes general status, time to next read, and exception info if applicable.

-}
getCurrentReads : CurrentReads -> Html msg
getCurrentReads currentReads =
    Grid.container [ style "padding" "1em" ]
        [ Grid.row [ Row.attrs [ class "align-items-center" ] ]
            [ Grid.col [ Col.attrs [ style "text-align" "center", style "padding" "2em" ] ]
                [ h1
                    [ style "color" (Maybe.map getColorForLevel currentReads.epaLevel |> Maybe.withDefault "black")
                    ]
                    [ text (Maybe.map String.fromFloat currentReads.lastEpaRead |> Maybe.withDefault "NA") ]
                ]
            ]
        , Grid.row [ Row.attrs [ class "align-items-center" ] ]
            [ Grid.col [ Col.attrs [ style "text-align" "center", style "padding-bottom" "2em" ] ] [ a [ href "https://www.airnow.gov/aqi/aqi-basics/" ] [ text "EPA AQI Score" ] ] ]
        , Grid.row [ Row.attrs [ class "align-items-center" ] ]
            [ Grid.col [ Col.attrs [ style "text-align" "right" ] ] [ text "Last PM10:" ]
            , Grid.col [ Col.attrs [ style "text-align" "center", style "font-weight" "bold" ] ] [ text (Maybe.map String.fromFloat currentReads.lastPm10 |> Maybe.withDefault "NA") ]
            ]
        , Grid.row [ Row.attrs [ class "align-items-center" ] ]
            [ Grid.col [ Col.attrs [ style "text-align" "right" ] ] [ text "Last PM25:" ]
            , Grid.col [ Col.attrs [ style "text-align" "center", style "font-weight" "bold" ] ] [ text (Maybe.map String.fromFloat currentReads.lastPm25 |> Maybe.withDefault "NA") ]
            ]
        ]


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
