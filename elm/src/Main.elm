module Main exposing (..)

import Bootstrap.Button as Button
import Bootstrap.ButtonGroup as ButtonGroup
import Bootstrap.Form.Select as Select
import Bootstrap.Grid as Grid
import Bootstrap.Grid.Col as Col
import Bootstrap.Grid.Row as Row
import Browser
import Chart.Item as CI
import CurrentReads as CR exposing (..)
import DeviceStatus as DS exposing (..)
import EpaCommon as EC exposing (..)
import EpaLevel as EL exposing (..)
import Graph as G exposing (..)
import Html exposing (Attribute, Html, div, h1, h2, h5, img, text)
import Html.Attributes exposing (class, height, src, style, value, width)
import Http
import Json.Decode exposing (Decoder, andThen, fail, field, float, int, list, map2, map3, map4, maybe, string, succeed)
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


type VisibleGraph
    = Epa
    | ParticleMatter


{-| Lastest data point
-}
type alias LatestData =
    { pm25 : Maybe Float
    , pm10 : Maybe Float
    , epa : Maybe Float
    , epaLevel : Maybe EpaLevel
    }


{-| Read data from the device
-}
type alias ReadData =
    { time : Float
    , pm25 : Float
    , pm10 : Float
    }


{-| EPA AQI data
-}
type alias EpaData =
    { time : Float
    , epa : Float
    }


{-| All data wrapper
-}
type alias AllData =
    { reads : List ReadData
    , epas : List EpaData
    }


{-| Hard error model. In cases where we have unexpected failures.
-}
type alias ErrorData =
    { hasError : Bool
    , errorTitle : String
    , errorMessage : String
    }


{-| Core model
-}
type alias Model =
    { currentTime : Maybe Posix
    , lastStatusPoll : Maybe Posix
    , readerState : DeviceInfo
    , lastReads : LatestData
    , allReads : List ReadData
    , allEpas : List EpaData
    , windowDuration : WindowDuration
    , dataLoading : Bool
    , hoveringReads : List (CI.One ReadData CI.Dot)
    , hoveringEpas : List (CI.One EpaData CI.Dot)
    , errorData : ErrorData
    , currentGraph : VisibleGraph
    , timeZone : Zone
    }


{-| Initial model state
-}
init : () -> ( Model, Cmd Msg )
init _ =
    ( { currentTime = Nothing
      , lastStatusPoll = Nothing
      , readerState = { state = Idle, lastException = Nothing, currentTime = Nothing, nextSchedule = Nothing }
      , lastReads = { pm25 = Nothing, pm10 = Nothing, epa = Nothing, epaLevel = Nothing }
      , allReads = []
      , allEpas = []
      , windowDuration = Hour
      , dataLoading = True
      , hoveringReads = []
      , hoveringEpas = []
      , errorData = { hasError = False, errorTitle = "", errorMessage = "" }
      , currentGraph = Epa
      , timeZone = utc
      }
    , Cmd.batch [ Task.perform FetchData Time.now, Task.perform FetchLatest Time.now, Task.perform GetTimeZone Time.here ]
    )


{-| Get read data for a given window duration.
-}
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
        , expect = Http.expectJson GotData allDataDecoder
        }


{-| Get latest read data.
-}
getLatest : Cmd Msg
getLatest =
    Http.get
        { url = "/api/latest_data"
        , expect = Http.expectJson GotLatest latestDataDecoder
        }


getStatus : Cmd Msg
getStatus =
    Http.get
        { url = "/api/status"
        , expect = Http.expectJson GotStatus statusDecoder
        }



-- UPDATE


{-| Possible update messages.
-}
type Msg
    = FetchData Posix
    | FetchLatest Posix
    | FetchStatus Posix
    | GetTimeZone Zone
    | GotData (Result Http.Error AllData)
    | GotLatest (Result Http.Error LatestData)
    | GotStatus (Result Http.Error DeviceInfoResponse)
    | ChangeWindow WindowDuration
    | OnReadHover (List (CI.One ReadData CI.Dot))
    | OnEpaHover (List (CI.One EpaData CI.Dot))
    | Tick Posix
    | ChangeGraphView String


{-| Core update handler.
-}
update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        GotData result ->
            -- On Data received
            case result of
                Ok data ->
                    ( { model | allReads = data.reads, allEpas = data.epas, dataLoading = False, errorData = { hasError = False, errorTitle = "", errorMessage = "" } }, Cmd.none )

                Err e ->
                    ( { model | dataLoading = False, errorData = { hasError = True, errorTitle = "Failed to retrieve read data", errorMessage = errorToString e } }, Cmd.none )

        FetchData newTime ->
            -- Data requested
            ( { model | currentTime = Just newTime, dataLoading = True }, getData model.windowDuration )

        GetTimeZone timeZone ->
            ( { model | timeZone = timeZone }, Cmd.none )

        GotLatest result ->
            case result of
                Ok data ->
                    ( { model | lastReads = data, errorData = { hasError = False, errorTitle = "", errorMessage = "" } }, Cmd.none )

                Err e ->
                    ( { model | errorData = { hasError = True, errorTitle = "Failed to retrieve latest data", errorMessage = errorToString e } }, Cmd.none )

        FetchLatest newTime ->
            ( { model | currentTime = Just newTime }, getLatest )

        GotStatus result ->
            case result of
                Ok data ->
                    let
                        deviceInfo =
                            { state = data.readerStatus
                            , lastException = data.readerException
                            , currentTime = model.currentTime
                            , nextSchedule = Maybe.map Time.millisToPosix data.nextSchedule
                            }
                    in
                    ( { model | readerState = deviceInfo, errorData = { hasError = False, errorTitle = "", errorMessage = "" } }, Cmd.none )

                Err e ->
                    ( { model | errorData = { hasError = True, errorTitle = "Failed to retrieve device status", errorMessage = errorToString e } }, Cmd.none )

        FetchStatus newTime ->
            -- Status Requested
            ( { model | currentTime = Just newTime, lastStatusPoll = Just newTime }, getStatus )

        ChangeWindow window ->
            -- Window duration changed
            ( { model | windowDuration = window }, Task.perform FetchData Time.now )

        OnReadHover hovering ->
            -- Hover over a datapoint on the read graph
            ( { model | hoveringReads = hovering }, Cmd.none )

        OnEpaHover hovering ->
            -- Hover over a datapoint on the EPA graph
            ( { model | hoveringEpas = hovering }, Cmd.none )

        Tick newTime ->
            let
                readerState =
                    model.readerState

                updatedReaderState =
                    { readerState | currentTime = Just newTime }

                cmd =
                    if shouldFetchStatus model newTime then
                        Task.perform FetchStatus Time.now

                    else
                        Cmd.none
            in
            ( { model | currentTime = Just newTime, readerState = updatedReaderState }, cmd )

        ChangeGraphView newView ->
            let
                newGraph =
                    if newView == "pm" then
                        ParticleMatter

                    else
                        Epa
            in
            ( { model | currentGraph = newGraph }, Cmd.none )



-- SUBSCRIPTIONS


{-| Root subscriptions.
-}
subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch [ Time.every 5000 FetchData, Time.every 5000 FetchLatest, Time.every 500 Tick ]



-- Get read data for the graph every 5 seconds.
-- VIEW


{-| Root view function
-}
view : Model -> Html Msg
view model =
    div []
        [ Grid.container [ style "margin-bottom" ".5em" ]
            [ Grid.row [ Row.attrs [ style "padding" "1em" ] ]
                [ Grid.col []
                    [ h1
                        [ class "d-flex", class "align-items-center" ]
                        [ img [ src "/static/images/aqimon.png", style "margin-right" "0.5em", width 75, height 75, class "d-inline-block", class "align-text-top" ] []
                        , text "AQI Monitor"
                        ]
                    ]
                ]
            , Grid.row [ Row.attrs [ style "padding" "1em" ] ]
                [ Grid.col [ Col.attrs [ style "background-color" "#D9D9D9", style "margin" "1em" ] ]
                    [ CR.getCurrentReads { epaLevel = model.lastReads.epaLevel, lastEpaRead = model.lastReads.epa, lastPm25 = model.lastReads.pm25, lastPm10 = model.lastReads.pm10 } ]
                , Grid.col [ Col.attrs [ class "align-items-center", class "d-flex", style "background-color" "#D9D9D9", style "margin" "1em" ] ]
                    [ EL.getEpaLevel model.lastReads.epaLevel ]
                , Grid.col [ Col.attrs [ style "background-color" "#D9D9D9", style "margin" "1em" ] ]
                    [ DS.getDeviceInfo model.readerState ]
                ]
            , htmlIf
                (Grid.row []
                    [ Grid.col [ Col.attrs [ class "alert", class "alert-danger" ] ]
                        [ h5 [] [ text model.errorData.errorTitle ]
                        , text model.errorData.errorMessage
                        ]
                    ]
                )
                model.errorData.hasError
            , Grid.row [ Row.attrs [ style "padding" "1em" ] ]
                [ Grid.col []
                    [ h2
                        []
                        [ text "History" ]
                    ]
                , Grid.col []
                    [ Select.select [ Select.onChange ChangeGraphView ]
                        [ Select.item [ value "epa" ] [ text "EPA AQI" ]
                        , Select.item [ value "pm" ] [ text "Particulate Matter" ]
                        ]
                    ]
                , Grid.col [ Col.lg3 ]
                    [ ButtonGroup.radioButtonGroup [ ButtonGroup.attrs [] ]
                        [ getSelector All "All" model.windowDuration
                        , getSelector Hour "Hour" model.windowDuration
                        , getSelector Day "Day" model.windowDuration
                        , getSelector Week "Week" model.windowDuration
                        ]
                    ]
                ]
            , htmlIf
                (Grid.row [ Row.attrs [ style "padding-top" "1em", style "padding-bottom" "3em" ], Row.centerMd ]
                    [ Grid.col [ Col.lg ]
                        [ div [ style "height" "400px" ]
                            [ G.getEpaChart { graphData = model.allEpas, currentHover = model.hoveringEpas, timeZone = model.timeZone, isLoading = model.dataLoading } OnEpaHover ]
                        ]
                    ]
                )
                (model.currentGraph == Epa)
            , htmlIf
                (Grid.row [ Row.attrs [ style "padding-top" "1em", style "padding-bottom" "3em" ], Row.centerMd ]
                    [ Grid.col [ Col.lg ]
                        [ div [ style "height" "400px" ]
                            [ G.getReadChart { graphData = model.allReads, currentHover = model.hoveringReads, timeZone = model.timeZone, isLoading = model.dataLoading } OnReadHover ]
                        ]
                    ]
                )
                (model.currentGraph == ParticleMatter)
            ]
        ]


{-| Get a button view for a window duration.
-}
getSelector : WindowDuration -> String -> WindowDuration -> ButtonGroup.RadioButtonItem Msg
getSelector windowDuration textDuration currentDuration =
    ButtonGroup.radioButton
        (windowDuration == currentDuration)
        [ Button.outlineDark, Button.onClick <| ChangeWindow windowDuration ]
        [ text textDuration ]


{-| Decoder function for JSON read data
-}
readDataDecoder : Decoder (List ReadData)
readDataDecoder =
    list
        (map3 ReadData
            (field "t" float)
            (field "pm25" float)
            (field "pm10" float)
        )


{-| Decoder function for JSON epa data
-}
epaDataDecoder : Decoder (List EpaData)
epaDataDecoder =
    list
        (map2 EpaData
            (field "t" float)
            (field "epa" float)
        )


allDataDecoder : Decoder AllData
allDataDecoder =
    map2 AllData
        (field "reads" readDataDecoder)
        (field "epas" epaDataDecoder)


latestDataDecoder : Decoder LatestData
latestDataDecoder =
    map4 LatestData
        (maybe (field "pm25" float))
        (maybe (field "pm10" float))
        (maybe (field "epa" float))
        (maybe (field "level" epaLevelDecoder))


type alias DeviceInfoResponse =
    { readerStatus : DS.DeviceState
    , readerException : Maybe String
    , nextSchedule : Maybe Int
    }


{-| Decoder function for JSON status data
-}
statusDecoder : Decoder DeviceInfoResponse
statusDecoder =
    map3 DeviceInfoResponse
        (field "reader_status" stateDecoder)
        (maybe (field "reader_exception" string))
        (maybe (field "next_schedule" int))


{-| JSON decoder to convert a device state to its type.
-}
stateDecoder : Decoder DS.DeviceState
stateDecoder =
    string
        |> andThen
            (\str ->
                case str of
                    "IDLE" ->
                        succeed DS.Idle

                    "WARM_UP" ->
                        succeed DS.WarmingUp

                    "ERRORING" ->
                        succeed DS.Failing

                    "READING" ->
                        succeed DS.Reading

                    _ ->
                        fail "Invalid DeviceState"
            )


{-| JSON decoder to convert a device state to its type.
-}
epaLevelDecoder : Decoder EpaLevel
epaLevelDecoder =
    string
        |> andThen
            (\str ->
                case str of
                    "HAZARDOUS" ->
                        succeed Hazardous

                    "VERY_UNHEALTHY" ->
                        succeed VeryUnhealthy

                    "UNHEALTHY" ->
                        succeed Unhealthy

                    "UNHEALTHY_FOR_SENSITIVE" ->
                        succeed UnhealthyForSensitive

                    "MODERATE" ->
                        succeed Moderate

                    "GOOD" ->
                        succeed Good

                    _ ->
                        fail "Invalid Epa Level"
            )


{-| Convert HTTP error to a string.
-}
errorToString : Http.Error -> String
errorToString error =
    case error of
        Http.BadUrl url ->
            "The URL " ++ url ++ " was invalid"

        Http.Timeout ->
            "Unable to reach the server, try again"

        Http.NetworkError ->
            "Unable to reach the server, check your network connection"

        Http.BadStatus 500 ->
            "The server had a problem, try again later"

        Http.BadStatus 400 ->
            "Verify your information and try again"

        Http.BadStatus _ ->
            "Unknown error"

        Http.BadBody errorMessage ->
            errorMessage


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
getDuration : Posix -> Posix -> Int
getDuration currentTime scheduledTime =
    let
        durationMillis =
            posixToMillis scheduledTime - posixToMillis currentTime
    in
    durationMillis


{-| Determine if we should fetch device status.
-}
shouldFetchStatus : Model -> Posix -> Bool
shouldFetchStatus model currentTime =
    let
        maxTimeBetweenPolls =
            15000

        timeSinceLastPoll =
            Maybe.map2 getDuration model.lastStatusPoll (Just currentTime) |> Maybe.withDefault (maxTimeBetweenPolls + 1)

        timeToNextRead =
            Maybe.map2 getDuration model.readerState.nextSchedule (Just currentTime) |> Maybe.withDefault 1
    in
    -- Reader state is active, we always want to see when it finishes ASAP.
    (model.readerState.state == Reading || model.readerState.state == WarmingUp)
        -- We're overdue for a poll
        || (timeSinceLastPoll > maxTimeBetweenPolls)
        -- We're overdue for a read
        || (timeToNextRead > -1)
