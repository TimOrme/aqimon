module Main exposing (..)

import Bootstrap.Button as Button
import Bootstrap.ButtonGroup as ButtonGroup
import Bootstrap.Grid as Grid
import Bootstrap.Grid.Col as Col
import Bootstrap.Grid.Row as Row
import Bootstrap.Text as Text
import Browser
import Chart.Item as CI
import DeviceStatus as DS exposing (..)
import Graph as G exposing (..)
import Html exposing (Attribute, Html, div, h1, h5, text)
import Html.Attributes exposing (class, style)
import Http
import Json.Decode exposing (Decoder, andThen, fail, field, float, int, list, map3, map4, maybe, string, succeed)
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


{-| Read data from the device
-}
type alias ReadData =
    { time : Float
    , epa : Float
    , pm25 : Float
    , pm10 : Float
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
    , lastReads : ReadData
    , allReads : List ReadData
    , windowDuration : WindowDuration
    , dataLoading : Bool
    , hovering : List (CI.One ReadData CI.Dot)
    , errorData : ErrorData
    }


{-| Initial model state
-}
init : () -> ( Model, Cmd Msg )
init _ =
    ( { currentTime = Nothing
      , lastStatusPoll = Nothing
      , readerState = { state = Idle, lastException = Nothing, currentTime = Nothing, nextSchedule = Nothing }
      , lastReads = { time = 0, epa = 0, pm25 = 0.0, pm10 = 0.0 }
      , allReads = []
      , windowDuration = Hour
      , dataLoading = True
      , hovering = []
      , errorData = { hasError = False, errorTitle = "", errorMessage = "" }
      }
    , Task.perform FetchData Time.now
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
        , expect = Http.expectJson GotData dataDecoder
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
    | FetchStatus Posix
    | GotData (Result Http.Error (List ReadData))
    | GotStatus (Result Http.Error DeviceInfoResponse)
    | ChangeWindow WindowDuration
    | OnHover (List (CI.One ReadData CI.Dot))
    | Tick Posix


{-| Core update handler.
-}
update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        GotData result ->
            -- On Data received
            case result of
                Ok data ->
                    ( { model | lastReads = getLastListItem data, allReads = data, errorData = { hasError = False, errorTitle = "", errorMessage = "" } }, Cmd.none )

                Err e ->
                    ( { model | errorData = { hasError = True, errorTitle = "Failed to retrieve read data", errorMessage = errorToString e } }, Cmd.none )

        FetchData newTime ->
            -- Data requested
            ( { model | currentTime = Just newTime }, getData model.windowDuration )

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

        OnHover hovering ->
            ( { model | hovering = hovering }, Cmd.none )

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



-- SUBSCRIPTIONS


{-| Root subscriptions.
-}
subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch [ Time.every 5000 FetchData, Time.every 500 Tick ]



-- Get read data for the graph every 5 seconds.
-- VIEW


{-| Root view function
-}
view : Model -> Html Msg
view model =
    div []
        [ Grid.container [ style "margin-bottom" ".5em" ]
            [ Grid.row [ Row.attrs [ class "bg-info", style "padding" "1em" ] ]
                [ Grid.col []
                    [ h1
                        [ class "text-center"
                        ]
                        [ text "AQI Monitor" ]
                    ]
                , Grid.col [] [ DS.getDeviceInfo model.readerState ]
                ]
            ]
        , htmlIf
            (Grid.container []
                [ Grid.row []
                    [ Grid.col [ Col.attrs [ class "alert", class "alert-danger" ] ]
                        [ h5 [] [ text model.errorData.errorTitle ]
                        , text model.errorData.errorMessage
                        ]
                    ]
                ]
            )
            model.errorData.hasError
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
                        [ G.getChart { graphData = model.allReads, currentHover = model.hovering } OnHover ]
                    ]
                ]
            ]
        ]


{-| Get a button view for a window duration.
-}
getSelector : WindowDuration -> String -> WindowDuration -> ButtonGroup.RadioButtonItem Msg
getSelector windowDuration textDuration currentDuration =
    ButtonGroup.radioButton
        (windowDuration == currentDuration)
        [ Button.outlinePrimary, Button.onClick <| ChangeWindow windowDuration ]
        [ text textDuration ]


{-| Get a "big number" view for the headline.
-}
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


{-| Decoder function for JSON read data
-}
dataDecoder : Decoder (List ReadData)
dataDecoder =
    list
        (map4 ReadData
            (field "t" float)
            (field "epa" float)
            (field "pm25" float)
            (field "pm10" float)
        )


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

                    "ERRORING" ->
                        succeed DS.Failing

                    "READING" ->
                        succeed DS.Reading

                    _ ->
                        fail "Invalid DeviceState"
            )


{-| Given a list of read data, retrieve the last item from that list.
Useful for grabbing the most recent read from the device.
If the list is empty, a read with all 0 values is returned.

getLastListItem [
{time = 1, epa = 1, pm25 = 1, pm 10 = 1},
{time = 2, epa = 2, pm25 = 2, pm 10 = 2},
{time = 3, epa = 3, pm25 = 3, pm 10 = 3},
] = [{time = 3, epa = 3, pm25 = 3, pm 10 = 3}]

-}
getLastListItem : List ReadData -> ReadData
getLastListItem myList =
    case List.head (List.reverse myList) of
        Just a ->
            a

        Nothing ->
            { time = 0, epa = 0, pm25 = 0, pm10 = 0 }


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
    (model.readerState.state == Reading)
        -- We're overdue for a poll
        || (timeSinceLastPoll > maxTimeBetweenPolls)
        -- We're overdue for a read
        || (timeToNextRead > -1)
