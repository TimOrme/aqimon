module Graph exposing (..)

import Chart as C
import Chart.Attributes as CA
import Chart.Events as CE
import Chart.Item as CI
import Html exposing (Attribute, Html)
import Html.Attributes exposing (style)
import Time exposing (..)


{-| A graph model, including all data for the read graph, as well as the current hover state.
-}
type alias GraphReadModel =
    { graphData : List GraphReadData
    , currentHover : List (CI.One GraphReadData CI.Dot)
    }


{-| A graph model, including all data for the EPA graph, as well as the current hover state.
-}
type alias GraphEpaModel =
    { graphData : List GraphEpaData
    , currentHover : List (CI.One GraphEpaData CI.Dot)
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
        [ C.xLabels [ CA.fontSize 10, CA.withGrid, CA.format formatTime ]
        , C.yLabels [ CA.fontSize 10, CA.withGrid ]
        , C.series .time
            [ C.interpolated .pm25 [ CA.monotone, CA.color CA.yellow ] [ CA.circle, CA.size 3 ] |> C.named "PM2.5"
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
        [ C.xLabels [ CA.fontSize 10, CA.withGrid, CA.format formatTime ]
        , C.yLabels [ CA.fontSize 10, CA.withGrid ]
        , C.series .time
            [ C.interpolated .epa [ CA.monotone, CA.color CA.blue ] [ CA.circle, CA.size 3 ] |> C.named "EPA"
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
