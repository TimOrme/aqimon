module EpaLevel exposing (..)

import Bootstrap.Grid as Grid
import Bootstrap.Grid.Col as Col
import Bootstrap.Grid.Row as Row
import EpaCommon exposing (..)
import Html exposing (Attribute, Html, a, div, h1, h5, img, text)
import Html.Attributes exposing (alt, class, href, src, style)


{-| HTML widget for displaying the device status.

Includes general status, time to next read, and exception info if applicable.

-}
getEpaLevel : Maybe EpaLevel -> Html msg
getEpaLevel currentLevel =
    Grid.container [ class "align-middle", style "padding" "1em" ]
        [ getRow Hazardous (currentLevel == Just Hazardous)
        , getRow VeryUnhealthy (currentLevel == Just VeryUnhealthy)
        , getRow Unhealthy (currentLevel == Just Unhealthy)
        , getRow UnhealthyForSensitive (currentLevel == Just UnhealthyForSensitive)
        , getRow Moderate (currentLevel == Just Moderate)
        , getRow Good (currentLevel == Just Good)
        ]


getRow : EpaLevel -> Bool -> Html msg
getRow level isSelected =
    Grid.row [ Row.attrs (List.append [ style "background-color" (getColorForLevel level) ] (selectedStyles isSelected)) ]
        [ Grid.col [ Col.attrs [ style "text-align" "center", style "padding" ".25em", style "color" "white" ] ] [ text (getLabelForLevel level) ] ]


selectedStyles : Bool -> List (Attribute msg)
selectedStyles isSelected =
    if isSelected then
        [ style "border-radius" "1em" ]

    else
        [ style "margin" "0 0.25em 0 0.25em" ]
