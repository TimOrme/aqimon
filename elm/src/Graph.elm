module Graph exposing (..)

import Chart as C
import Chart.Attributes as CA
import Chart.Events as CE
import Chart.Item as CI
import Html exposing (Attribute, Html, br, div, p, span, text)
import Html.Attributes exposing (style)
import Time exposing (..)


{-| A graph model, including all data for the read graph, as well as the current hover state.
-}
type alias GraphReadModel =
    { graphData : List GraphReadData
    , currentHover : List (CI.One GraphReadData CI.Dot)
    , timeZone : Zone
    }


{-| A graph model, including all data for the EPA graph, as well as the current hover state.
-}
type alias GraphEpaModel =
    { graphData : List GraphEpaData
    , currentHover : List (CI.One GraphEpaData CI.Dot)
    , timeZone : Zone
    }


{-| Graph data, representing a point on the graph.
-}
type alias GraphReadData =
    { time : Float
    , pm25 : Float
    , pm10 : Float
    }


{-| Graph data, representing a point on the graph.
-}
type alias GraphEpaData =
    { time : Float
    , epa : Float
    }


{-| Get a chart of read data.

Accepts a model of graph data, and an event that occurs on graph hover.

-}
getReadChart : GraphReadModel -> (List (CI.One GraphReadData CI.Dot) -> msg) -> Html msg
getReadChart graphModel onHover =
    C.chart
        [ CA.height 200
        , CA.width 800
        , CA.margin { left = 40, top = 0, right = 20, bottom = 0 }
        , CE.onMouseMove onHover (CE.getNearest CI.dots)
        , CE.onMouseLeave (onHover [])
        ]
        [ C.xLabels [ CA.fontSize 10, CA.withGrid, CA.format (\time -> formatTime time graphModel.timeZone) ]
        , C.yLabels [ CA.fontSize 10, CA.withGrid ]
        , C.series .time
            [ C.interpolated .pm25 [ CA.monotone, CA.color CA.yellow ] [ CA.circle, CA.size 3 ] |> C.named "PM2.5"
            , C.interpolated .pm10 [ CA.monotone, CA.color CA.red ] [ CA.circle, CA.size 3 ] |> C.named "PM10"
            ]
            graphModel.graphData
        , C.each graphModel.currentHover <|
            \p item ->
                [ C.tooltip item [] [] (getPmToolTip item graphModel.timeZone) ]
        , C.legendsAt .min
            .max
            [ CA.row -- Appear as column instead of row
            , CA.alignLeft -- Anchor legends to the right
            , CA.spacing 5 -- Spacing between legends
            , CA.background "Azure" -- Color background
            , CA.border "gray" -- Add border
            , CA.borderWidth 1 -- Set border width
            , CA.htmlAttrs [ style "padding" "0px 4px" ]
            ]
            [ CA.fontSize 12 -- Change font size
            ]
        ]


{-| Get a chart of read data.

Accepts a model of graph data, and an event that occurs on graph hover.

-}
getEpaChart : GraphEpaModel -> (List (CI.One GraphEpaData CI.Dot) -> msg) -> Html msg
getEpaChart graphModel onHover =
    C.chart
        [ CA.height 200
        , CA.width 800
        , CA.margin { left = 40, top = 0, right = 20, bottom = 0 }
        , CE.onMouseMove onHover (CE.getNearest CI.dots)
        , CE.onMouseLeave (onHover [])
        ]
        [ C.xLabels [ CA.fontSize 10, CA.withGrid, CA.format (\time -> formatTime time graphModel.timeZone) ]
        , C.yLabels [ CA.fontSize 10, CA.withGrid ]
        , C.series .time
            [ C.interpolated .epa [ CA.monotone, CA.color CA.blue ] [ CA.circle, CA.size 3 ] |> C.named "EPA"
            ]
            graphModel.graphData
        , C.each graphModel.currentHover <|
            \p item ->
                [ C.tooltip item [] [] (getEpaToolTip item graphModel.timeZone) ]
        , C.legendsAt .min
            .max
            [ CA.row -- Appear as column instead of row
            , CA.alignLeft -- Anchor legends to the right
            , CA.spacing 5 -- Spacing between legends
            , CA.background "Azure" -- Color background
            , CA.border "gray" -- Add border
            , CA.borderWidth 1 -- Set border width
            , CA.htmlAttrs [ style "padding" "0px 4px" ]
            ]
            [ CA.fontSize 12 -- Change font size
            ]
        ]


getEpaToolTip : CI.One GraphEpaData CI.Dot -> Zone -> List (Html msg)
getEpaToolTip item timeZone =
    let
        data =
            CI.getData item

        color =
            CI.getColor item

        value =
            String.fromFloat data.epa

        formattedTime =
            formatTime data.time timeZone
    in
    [ div []
        [ span [ style "color" color ] [ text "EPA" ]
        , span [] [ text (": " ++ value) ]
        , br [] []
        , span [ style "color" color ] [ text "Time" ]
        , span [] [ text (": " ++ formattedTime) ]
        ]
    ]


getPmToolTip : CI.One GraphReadData CI.Dot -> Zone -> List (Html msg)
getPmToolTip item timeZone =
    let
        data =
            CI.getData item

        color =
            CI.getColor item

        value =
            CI.getTooltipValue item

        label =
            CI.getName item

        formattedTime =
            formatTime data.time timeZone
    in
    [ div []
        [ span [ style "color" color ] [ text label ]
        , span [] [ text (": " ++ value) ]
        , br [] []
        , span [ style "color" color ] [ text "Time" ]
        , span [] [ text (": " ++ formattedTime) ]
        ]
    ]


{-| Format a unix timestamp as a string like MM/DD HH:MM:SS
-}
formatTime : Float -> Zone -> String
formatTime time timeZone =
    let
        milliTime =
            Time.millisToPosix (floor time * 1000)

        year =
            String.fromInt (toYear timeZone milliTime)

        month =
            monthToString (toMonth timeZone milliTime)

        day =
            String.fromInt (toDay timeZone milliTime)

        hour =
            String.pad 2 '0' (String.fromInt (toHour timeZone milliTime))

        minute =
            String.pad 2 '0' (String.fromInt (toMinute timeZone milliTime))

        second =
            String.pad 2 '0' (String.fromInt (toSecond timeZone milliTime))
    in
    month ++ "/" ++ day ++ " " ++ hour ++ ":" ++ minute ++ ":" ++ second


{-| Convert a month to a string value. In this case, to a 2 digit numeric representation
-}
monthToString : Month -> String
monthToString month =
    case month of
        Jan ->
            "01"

        Feb ->
            "02"

        Mar ->
            "03"

        Apr ->
            "04"

        May ->
            "05"

        Jun ->
            "06"

        Jul ->
            "07"

        Aug ->
            "08"

        Sep ->
            "09"

        Oct ->
            "10"

        Nov ->
            "11"

        Dec ->
            "12"
