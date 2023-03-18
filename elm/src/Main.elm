module Main exposing (..)

import Bootstrap.Button as Button
import Bootstrap.ButtonGroup as ButtonGroup
import Bootstrap.Grid as Grid
import Bootstrap.Grid.Col as Col
import Bootstrap.Grid.Row as Row
import Bootstrap.Text as Text
import Browser
import Chart as C
import Chart.Attributes as CA
import Html exposing (Attribute, Html, div, h1, h5, text)
import Html.Attributes exposing (class, style)
import Http
import Json.Decode exposing (Decoder, field, float, list, map4)
import Task
import Time exposing (..)



-- MAIN


main =
    Browser.element
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }



-- MODEL


type WindowDuration
    = All
    | Hour
    | Day
    | Week


type alias ReaderState =
    { status : String
    , lastException : String
    }


type alias ReadData =
    { time : Float
    , epa : Float
    , pm25 : Float
    , pm10 : Float
    }


type alias Model =
    { currentTime : Maybe Posix
    , readerState : ReaderState
    , lastReads : ReadData
    , allReads : List ReadData
    , windowDuration : WindowDuration
    , dataLoading : Bool
    }


init : () -> ( Model, Cmd Msg )
init _ =
    ( { currentTime = Nothing
      , readerState = { status = "IDLE", lastException = "" }
      , lastReads = { time = 0, epa = 0, pm25 = 0.0, pm10 = 0.0 }
      , allReads = []
      , windowDuration = Hour
      , dataLoading = True
      }
    , Task.perform FetchData Time.now
    )


getData : WindowDuration -> Cmd Msg
getData windowDuration =
    let
        stringDuration =
            case windowDuration of
                All ->
                    "all"

                Hour ->
                    "hour"

                Day ->
                    "day"

                Week ->
                    "week"
    in
    Http.get
        { url = "/api/sensor_data?window=" ++ stringDuration
        , expect = Http.expectJson GotData dataDecoder
        }



-- UPDATE


type Msg
    = FetchData Posix
    | GotData (Result Http.Error (List ReadData))
    | ChangeWindow WindowDuration


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        GotData result ->
            case result of
                Ok data ->
                    ( { model | lastReads = getLastListItem data, allReads = data }, Cmd.none )

                Err e ->
                    --let
                    -- _ =
                    --Debug.log "Error" (Debug.toString e)
                    -- in
                    ( model, Cmd.none )

        FetchData newTime ->
            ( { model | currentTime = Just newTime }, getData model.windowDuration )

        ChangeWindow window ->
            ( { model | windowDuration = window }, Task.perform FetchData Time.now )



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    Time.every 5000 FetchData



-- VIEW


view : Model -> Html Msg
view model =
    div []
        [ h1
            [ class "bg-primary text-center"
            , style "padding" ".25em"
            , style "margin-bottom" ".5em"
            , style "border-bottom" "1px solid darkgray"
            ]
            [ text "AQI Monitor" ]
        , Grid.container []
            [ Grid.row [ Row.centerMd ]
                [ Grid.col [ Col.lg3 ] [ viewBigNumber model.lastReads.epa "EPA" ]
                , Grid.col [ Col.lg3 ] [ viewBigNumber model.lastReads.pm25 "PM2.5" ]
                , Grid.col [ Col.lg3 ] [ viewBigNumber model.lastReads.pm10 "PM10" ]
                ]
            , Grid.row [ Row.attrs [ style "padding-top" "1em", class "justify-content-end" ] ]
                [ Grid.col [ Col.lg3 ]
                    [ ButtonGroup.radioButtonGroup []
                        [ getSelector All "All" model.windowDuration
                        , getSelector Hour "Hour" model.windowDuration
                        , getSelector Day "Day" model.windowDuration
                        , getSelector Week "Week" model.windowDuration
                        ]
                    ]
                ]
            , Grid.row [ Row.attrs [ style "padding-top" "1em" ], Row.centerMd ]
                [ Grid.col [ Col.lg ]
                    [ div [ style "height" "400px" ]
                        [ C.chart
                            [ CA.height 300
                            , CA.width 1000
                            ]
                            [ C.xLabels [ CA.moveDown 25, CA.withGrid, CA.rotate 60, CA.format formatTime ]
                            , C.yLabels [ CA.withGrid ]
                            , C.series .time
                                [ C.interpolated .epa [ CA.monotone, CA.color CA.blue ] []
                                , C.interpolated .pm25 [ CA.monotone, CA.color CA.yellow ] []
                                , C.interpolated .pm10 [ CA.monotone, CA.color CA.red ] []
                                ]
                                model.allReads
                            ]
                        ]
                    ]
                ]
            ]
        ]


getSelector : WindowDuration -> String -> WindowDuration -> ButtonGroup.RadioButtonItem Msg
getSelector windowDuration textDuration currentDuration =
    ButtonGroup.radioButton
        (windowDuration == currentDuration)
        [ Button.outlinePrimary, Button.onClick <| ChangeWindow windowDuration ]
        [ text textDuration ]


viewBigNumber : Float -> String -> Html Msg
viewBigNumber value numberType =
    Grid.container [ style "background-clip" "border-box", style "border" "1px solid darkgray", style "padding" "0", style "border-radius" ".25rem" ]
        [ Grid.row []
            [ Grid.col
                [ Col.textAlign Text.alignMdCenter ]
                [ h1
                    [ style "padding" ".5em"
                    , style "margin" "0"
                    , style "color" "white"
                    , style "background-color" "lightblue"
                    ]
                    [ text (String.fromFloat value) ]
                ]
            ]
        , Grid.row []
            [ Grid.col
                [ Col.textAlign Text.alignMdCenter ]
                [ h5
                    [ style "padding" ".25em"
                    , style "margin" "0"
                    , style "color" "darkblue"
                    , style "background-color" "lightgray"
                    ]
                    [ text numberType ]
                ]
            ]
        ]


dataDecoder : Decoder (List ReadData)
dataDecoder =
    list
        (map4 ReadData
            (field "t" float)
            (field "epa" float)
            (field "pm25" float)
            (field "pm10" float)
        )


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


getLastListItem : List ReadData -> ReadData
getLastListItem myList =
    case List.head (List.reverse myList) of
        Just a ->
            a

        Nothing ->
            { time = 0, epa = 0, pm25 = 0, pm10 = 0 }
