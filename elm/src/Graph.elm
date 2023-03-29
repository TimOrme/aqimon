module Graph exposing (..)

import Chart as C
import Chart.Attributes as CA
import Chart.Events as CE
import Chart.Item as CI
import Html exposing (Attribute, Html)
import Html.Attributes exposing (style)
import Time exposing (..)


{-| A graph model, including all data for the graph, as well as the current hover state.
-}
type alias GraphModel =
    { graphData : List GraphData
    , currentHover : List (CI.One GraphData CI.Dot)
    }


{-| Graph data, representing a point on the graph.
-}
type alias GraphData =
    { time : Float
    , epa : Float
    , pm25 : Float
    , pm10 : Float
    }


{-| Get a chart of read data.

Accepts a model of graph data, and an event that occurs on graph hover.

-}
getChart : GraphModel -> (List (CI.One GraphData CI.Dot) -> msg) -> Html msg
getChart graphModel onHover =
    C.chart
        [ CA.height 300
        , CA.width 1000
        , CE.onMouseMove onHover (CE.getNearest CI.dots)
        , CE.onMouseLeave (onHover [])
        ]
        [ C.xLabels [ CA.moveDown 25, CA.withGrid, CA.rotate 60, CA.format formatTime ]
        , C.yLabels [ CA.withGrid ]
        , C.series .time
            [ C.interpolated .epa [ CA.monotone, CA.color CA.blue ] [ CA.circle, CA.size 3 ] |> C.named "EPA"
            , C.interpolated .pm25 [ CA.monotone, CA.color CA.yellow ] [ CA.circle, CA.size 3 ] |> C.named "PM2.5"
            , C.interpolated .pm10 [ CA.monotone, CA.color CA.red ] [ CA.circle, CA.size 3 ] |> C.named "PM10"
            ]
            graphModel.graphData
        , C.each graphModel.currentHover <|
            \p item ->
                [ C.tooltip item [] [] [] ]
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


{-| Format a unix timestamp as a string like MM/DD HH:MM:SS
-}
formatTime : Float -> String
formatTime time =
    let
        milliTime =
            Time.millisToPosix (floor time * 1000)

        year =
            String.fromInt (toYear utc milliTime)

        month =
            monthToString (toMonth utc milliTime)

        day =
            String.fromInt (toDay utc milliTime)

        hour =
            String.fromInt (toHour utc milliTime)

        minute =
            String.fromInt (toMinute utc milliTime)

        second =
            String.fromInt (toSecond utc milliTime)
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
