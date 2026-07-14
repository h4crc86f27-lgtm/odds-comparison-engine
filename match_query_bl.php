
<?php

$very_start = microtime(true);

//ini_set('display_errors', 1); ini_set('display_startup_errors', 1); error_reporting(E_ALL);
session_start();

$url_components = parse_url($_SERVER['REQUEST_URI']);
parse_str($url_components['query'], $params);
$bf_sort = $params['bf_sort'];



$userid = $_SESSION['id'];// $_GET['user'];

$market = $_GET['market'];

$currency_conversion_rate=1;


//here setup constants for different markets..


if ($market==="1x2"){
	$howmanyways=3;
	$betfair_market_constant_a="bf_1_odds";
	$betfair_market_constant_b="bf_x_odds";
	$betfair_market_constant_c="bf_2_odds";
	
	$contra_market_constant_a="contra_1_odds";
	$contra_market_constant_b="contra_x_odds";
	$contra_market_constant_c="contra_2_odds";

	$toto_market_constant_a="toto_1_odds";
	$toto_market_constant_b="toto_x_odds";
	$toto_market_constant_c="toto_2_odds";

	$unibet_market_constant_a="unibet_1_odds";
	$unibet_market_constant_b="unibet_x_odds";
	$unibet_market_constant_c="unibet_2_odds";

	$qrbet_market_constant_a="qrbet_1_odds";
	$qrbet_market_constant_b="qrbet_x_odds";
	$qrbet_market_constant_c="qrbet_2_odds";

	$winkel_toto_market_constant_a="winkel_toto_1_odds";
	$winkel_toto_market_constant_b="winkel_toto_x_odds";
	$winkel_toto_market_constant_c="winkel_toto_2_odds";

	$bingoal_market_constant_a="bingoal_1_odds";
	$bingoal_market_constant_b="bingoal_x_odds";
	$bingoal_market_constant_c="bingoal_2_odds";

	$yess365_market_constant_a="yess365_1_odds";
	$yess365_market_constant_b="yess365_x_odds";
	$yess365_market_constant_c="yess365_2_odds";

	$betalpha_market_constant_a="betalpha_1_odds";
	$betalpha_market_constant_b="betalpha_x_odds";
	$betalpha_market_constant_c="betalpha_2_odds";

	$bet3000_market_constant_a="bet3000_1_odds";
	$bet3000_market_constant_b="bet3000_x_odds";
	$bet3000_market_constant_c="bet3000_2_odds";

	$m8bets_market_constant_a="m8bets_1_odds";
	$m8bets_market_constant_b="m8bets_x_odds";
	$m8bets_market_constant_c="m8bets_2_odds";

	$bet635_market_constant_a="bet635_1_odds";
	$bet635_market_constant_b="bet635_x_odds";
	$bet635_market_constant_c="bet635_2_odds";

	$live90bet_market_constant_a="polymarket_1_odds";
	$live90bet_market_constant_b="polymarket_x_odds";
	$live90bet_market_constant_c="polymarket_2_odds";

	/* add 1x2 constants */



	$header_a="1";
	$header_b="x";
	$header_c="2";
	$historical_a = "1";
	$historical_b = "X";
	$historical_c = "2";
	$bf_historical_a = "lowest_back_price_1";
	$bf_historical_b = "lowest_back_price_2";
	$bf_historical_c = "lowest_back_price_x";

} else if ($market==="dnb") {
	$howmanyways=2;
	$betfair_market_constant_a="bf_dnb_home";
	$betfair_market_constant_b="bf_dnb_away";
	
	$contra_market_constant_a="contra_dnb_home";
	$contra_market_constant_b="contra_dnb_away";

	$toto_market_constant_a="toto_dnb_home";
	$toto_market_constant_b="toto_dnb_away";

	$unibet_market_constant_a="unibet_dnb_home";
	$unibet_market_constant_b="unibet_dnb_away";

	$qrbet_market_constant_a="qrbet_dnb_home";
	$qrbet_market_constant_b="qrbet_dnb_away";

	$winkel_toto_market_constant_a="winkel_toto_dnb_home";
	$winkel_toto_market_constant_b="winkel_toto_dnb_away";
	
	$bingoal_market_constant_a="bingoal_dnb_home";
	$bingoal_market_constant_b="bingoal_dnb_away";

	$yess365_market_constant_a="yess365_dnb_home";
	$yess365_market_constant_b="yess365_dnb_away";

	$betalpha_market_constant_a="betalpha_dnb_home";
	$betalpha_market_constant_b="betalpha_dnb_away";

	$bet3000_market_constant_a="bet3000_dnb_home";
	$bet3000_market_constant_b="bet3000_dnb_away";

	$m8bets_market_constant_a="m8bets_dnb_home";
	$m8bets_market_constant_b="m8bets_dnb_away";

	$bet635_market_constant_a="bet635_dnb_home";
	$bet635_market_constant_b="bet635_dnb_away";

	$live90bet_market_constant_a="live90bet_dnb_home";
	$live90bet_market_constant_b="live90bet_dnb_away";

	/* add dnb constants */


	$header_a="1";
	$header_b="2";

	$historical_a = "DNB_Home";
	$historical_b = "DNB_Away";
	$bf_historical_a = "lowest_back_price_dnb_home";
	$bf_historical_b = "lowest_back_price_dnb_away";

//echo "im in market dnb with:".$howmanyways." ways";


} else if ($market==="uo2.5") {
	$howmanyways=2;
	$betfair_market_constant_a="bf_Under_2.5";
	$betfair_market_constant_b="bf_Over_2.5";
	
	$contra_market_constant_a="contra_under_2.5";
	$contra_market_constant_b="contra_over_2.5";

	$toto_market_constant_a="toto_under_2.5";
	$toto_market_constant_b="toto_over_2.5";

	$unibet_market_constant_a="unibet_under_2.5";
	$unibet_market_constant_b="unibet_over_2.5";

	$qrbet_market_constant_a="qrbet_under_2.5";
	$qrbet_market_constant_b="qrbet_over_2.5";

	$winkel_toto_market_constant_a="winkel_toto_under_2.5";
	$winkel_toto_market_constant_b="winkel_toto_over_2.5";
	
	$bingoal_market_constant_a="bingoal_under_2.5";
	$bingoal_market_constant_b="bingoal_over_2.5";

	$yess365_market_constant_a="yess365_under_2.5";
	$yess365_market_constant_b="yess365_over_2.5";

	$betalpha_market_constant_a="betalpha_under_2.5";
	$betalpha_market_constant_b="betalpha_over_2.5";

	$bet3000_market_constant_a="bet3000_under_2.5";
	$bet3000_market_constant_b="bet3000_over_2.5";
	$m8bets_market_constant_a="m8bets_under_2.5";
	$m8bets_market_constant_b="m8bets_over_2.5";

	$bet635_market_constant_a="bet635_under_2.5";
	$bet635_market_constant_b="bet635_over_2.5";

	$live90bet_market_constant_a="live90bet_under_2.5";
	$live90bet_market_constant_b="live90bet_over_2.5";

	/* add uo25 constants  */


	$header_a="u";
	$header_b="o";
	$historical_a = "2.5_Under";
	$historical_b = "2.5_Over";

	$bf_historical_a = "lowest_back_price_Under_2.5";
	$bf_historical_b = "lowest_back_price_Over_2.5";
} else if ($market==="uo3.5") {
	$howmanyways=2;
	$betfair_market_constant_a="bf_Under_3.5";
	$betfair_market_constant_b="bf_Over_3.5";
	
	$contra_market_constant_a="contra_under_3.5";
	$contra_market_constant_b="contra_over_3.5";

	$toto_market_constant_a="toto_under_3.5";
	$toto_market_constant_b="toto_over_3.5";

	$unibet_market_constant_a="unibet_under_3.5";
	$unibet_market_constant_b="unibet_over_3.5";

	$qrbet_market_constant_a="qrbet_under_3.5";
	$qrbet_market_constant_b="qrbet_over_3.5";

	$winkel_toto_market_constant_a="winkel_toto_under_3.5";
	$winkel_toto_market_constant_b="winkel_toto_over_3.5";
	
	$bingoal_market_constant_a="bingoal_under_3.5";
	$bingoal_market_constant_b="bingoal_over_3.5";

	$betalpha_market_constant_a="betalpha_under_3.5";
	$betalpha_market_constant_b="betalpha_over_3.5";

	
	$header_a="u";
	$header_b="o";

	$historical_a = "3.5_Under";
	$historical_b = "3.5_Over";
	
	$bf_historical_a = "lay_price_Under_3.5";
	$bf_historical_b = "lay_price_Over_3.5";
	

} else if ($market==="dc"){
	$howmanyways=3;
	$betfair_market_constant_a="bf_dc_1x";
	$betfair_market_constant_b="bf_dc_x2";
	$betfair_market_constant_c="bf_dc_12";
	
	$contra_market_constant_a="contra_dc_1x";
	$contra_market_constant_b="contra_dc_x2";
	$contra_market_constant_c="contra_dc_12";

	$toto_market_constant_a="toto_dc_1x";
	$toto_market_constant_b="toto_dc_x2";
	$toto_market_constant_c="toto_dc_12";

	$unibet_market_constant_a="unibet_dc_1x";
	$unibet_market_constant_b="unibet_dc_x2";
	$unibet_market_constant_c="unibet_dc_12";

	$qrbet_market_constant_a="qrbet_dc_1x";
	$qrbet_market_constant_b="qrbet_dc_x2";
	$qrbet_market_constant_c="qrbet_dc_12";

	$winkel_toto_market_constant_a="winkel_toto_dc_1x";
	$winkel_toto_market_constant_b="winkel_toto_dc_x2";
	$winkel_toto_market_constant_c="winkel_toto_dc_12";

	$bingoal_market_constant_a="bingoal_dc_1x";
	$bingoal_market_constant_b="bingoal_dc_x2";
	$bingoal_market_constant_c="bingoal_dc_12";

	$betalpha_market_constant_a="betalpha_dc_1x";
	$betalpha_market_constant_b="betalpha_dc_x2";
	$betalpha_market_constant_c="betalpha_dc_12";


	$header_a="1x";
	$header_b="x2";
	$header_c="12";
	$historical_a = "DC_1X";
	$historical_b = "DC_X2";
	$historical_c = "DC_12";
	$bf_historical_a = "lay_price_DC_1X";
	$bf_historical_b = "lay_price_DC_X2";
	$bf_historical_c = "lay_price_DC_12";

}  else if ($market==="ht"){
	$howmanyways=3;
	$betfair_market_constant_a="bf_1_ht";
	$betfair_market_constant_b="bf_x_ht";
	$betfair_market_constant_c="bf_2_ht";
	
	$contra_market_constant_a="contra_1_ht";
	$contra_market_constant_b="contra_x_ht";
	$contra_market_constant_c="contra_2_ht";

	$toto_market_constant_a="toto_1_ht";
	$toto_market_constant_b="toto_x_ht";
	$toto_market_constant_c="toto_2_ht";

	$unibet_market_constant_a="unibet_1_ht";
	$unibet_market_constant_b="unibet_x_ht";
	$unibet_market_constant_c="unibet_2_ht";

	$qrbet_market_constant_a="qrbet_1_ht";
	$qrbet_market_constant_b="qrbet_x_ht";
	$qrbet_market_constant_c="qrbet_2_ht";

	$winkel_toto_market_constant_a="winkel_toto_1_ht";
	$winkel_toto_market_constant_b="winkel_toto_x_ht";
	$winkel_toto_market_constant_c="winkel_toto_2_ht";

	$bingoal_market_constant_a="bingoal_1_ht";
	$bingoal_market_constant_b="bingoal_x_ht";
	$bingoal_market_constant_c="bingoal_2_ht";

	$betalpha_market_constant_a="betalpha_1_ht";
	$betalpha_market_constant_b="betalpha_x_ht";
	$betalpha_market_constant_c="betalpha_2_ht";


	$m8bets_market_constant_a="m8bets_1_ht";
	$m8bets_market_constant_b="m8bets_x_ht";
	$m8bets_market_constant_c="m8bets_2_ht";
	
	$header_a="1_ht";
	$header_b="x_ht";
	$header_c="2_ht";
	$historical_a = "1_ht";
	$historical_b = "X_ht";
	$historical_c = "2_ht";
	$bf_historical_a = "lay_price_1_ht";
	$bf_historical_b = "lay_price_x_ht";
	$bf_historical_c = "lay_price_2_ht";

} 

$db_name = "arb_db_beta";
$time = time();
$conn = mysqli_connect('localhost','local','oeijifjwejfio',$db_name);

if ($conn->connect_error) {
  die("Connection failed: " . $conn->connect_error);
}

//here select which books to show..

/* add book user view */
$sql = "select toto,unibet,contra,qrbet,winkeltoto,bingoal,yess365,betalpha,bet3000,avg,m8bets,bet635,live90bet from user_views where user=".$userid;
$result = $conn->query($sql);
$row = $result->fetch_array(MYSQLI_BOTH);

$show_toto = $row['toto'];
$show_unibet = $row['unibet'];
$show_contra = $row['contra'];
$show_qrbet = $row['qrbet'];
$show_winkel_toto = $row['winkeltoto'];
$show_avg = $row['avg'];
$show_bingoal = $row['bingoal'];
$show_yess365=$row['yess365'];
$show_betalpha=$row['betalpha'];
$show_bet3000=$row['bet3000'];
$show_m8bets=$row['m8bets'];
$show_bet635=$row['bet635'];
$show_live90bet=$row['live90bet'];

/* add show book */



//       toto/unibet/contra

//$sql = "select * from unibet_matches a, toto_matches b, contra_matches c where b.ignored=0 and b.timestamp>'".$time."' and a.betfair_event_id=b.betfair_event_id and b.betfair_event_id=c.betfair_event_id order by b.timestamp asc";
//here find ignored comps..

$ignored_comps=array();


$sql = "select betfair_name from comps where ignore_comp=1";
$result = $conn->query($sql);
while ($row = $result->fetch_array(MYSQLI_BOTH)){
	$ignored_comps[] = $row[0];
}



$start_time = microtime(true);

//$sql = "select * from bf_ids left join toto_matches toto on bf_ids.betfair_event_id = toto.betfair_event_id left join unibet_matches unibet on bf_ids.betfair_event_id=unibet.betfair_event_id left join contra_matches contra on bf_ids.betfair_event_id = contra.betfair_event_id left join qrbet_matches qrbet on bf_ids.betfair_event_id = qrbet.betfair_event_id  left join winkel_toto_matches winkel_toto on bf_ids.betfair_event_id = winkel_toto.betfair_event_id   left join bingoal_matches bingoal on bf_ids.betfair_event_id = bingoal.betfair_event_id   left join yess365_matches yess365 on bf_ids.betfair_event_id = yess365.betfair_event_id  left join betalpha_matches betalpha on bf_ids.betfair_event_id = betalpha.betfair_event_id  left join bet3000_matches bet3000 on bf_ids.betfair_event_id = bet3000.betfair_event_id where (qrbet.timestamp>'".$time."' or toto.timestamp>'".$time."' or unibet.timestamp>'".$time."' or contra.timestamp>'".$time."' or winkel_toto.timestamp>'".$time."' or bingoal.timestamp>'".$time."' or yess365.timestamp>'".$time."') and bingoal.ignored=0";
/* add left join */
$sql = "select * from bf_ids  left join toto_matches toto on bf_ids.betfair_event_id = toto.betfair_event_id left join unibet_matches unibet on bf_ids.betfair_event_id=unibet.betfair_event_id left join contra_matches contra on bf_ids.betfair_event_id = contra.betfair_event_id  left join bet635_matches bet635 on bf_ids.betfair_event_id = bet635.betfair_event_id left join qrbet_matches qrbet on bf_ids.betfair_event_id = qrbet.betfair_event_id left join winkel_toto_matches winkel_toto on bf_ids.betfair_event_id = winkel_toto.betfair_event_id   left join bingoal_matches bingoal on bf_ids.betfair_event_id = bingoal.betfair_event_id   left join yess365_matches yess365 on bf_ids.betfair_event_id = yess365.betfair_event_id  left join betalpha_matches betalpha on bf_ids.betfair_event_id = betalpha.betfair_event_id  left join bet3000_matches bet3000 on bf_ids.betfair_event_id = bet3000.betfair_event_id left join m8bets_matches m8bets on bf_ids.betfair_event_id = m8bets.betfair_event_id left join polymarket_matches live90bet on bf_ids.betfair_event_id = live90bet.betfair_event_id";// where bingoal.ignored=0";

////echo $sql;

$result = $conn->query($sql);


$end_time = microtime(true);
$elapsed_time = $end_time - $start_time;
#echo "Query took " . $elapsed_time . " seconds to execute.";

$red_matches = array();
$green_matches = array();
$regular_matches = array();

$matched_matches=array();

$start_time = microtime(true);
while ($row = $result->fetch_array(MYSQLI_BOTH)){
	$matched_matches[]=$row[0];//'betfair_event_id'];

	//echo $row[3].$row[5]."<>".$row[6]."||".$row['betfair_event_id'];//." == ".var_dump($row[9])."<br>";
/*
	$arJson = json_decode( $row[9], true );
	if (count($arJson)>0){
		//fine
		//echo "9fine";
	} else {
		$arJson = json_decode( $row[22], true );
		if (count($arJson)>0){
			//fine
		//	echo "22fine";
		} else {
			$arJson = json_decode( $row[35], true );
			if (count($arJson)>0){
				//fine
			} else {
				$arJson = json_decode( $row[47], true );
				if (count($arJson)>0){
					//fine
				} else {
					$arJson = json_decode( $row[60], true );
				}
			}
		}
	}*/
	$arJson_toto = json_decode( $row['odds_data'], true );
	$arJson_unibet = json_decode( $row['unibet_data'], true );
	$arJson_contra = json_decode( $row['contra_data'], true );
	$arJson_qrbet= json_decode( $row['qrbet_data'], true );
	$arJson_winkel_toto= json_decode( $row['winkel_toto_data'], true );
	$arJson_bingoal= json_decode( $row['bingoal_data'], true );
	$arJson_yess365= json_decode( $row['yess365_data'], true );
	$arJson_betalpha= json_decode( $row['betalpha_data'], true );
	$arJson_bet3000= json_decode( $row['bet3000_data'], true );
	$arJson_m8bets= json_decode( $row['m8bets_data'], true );
	$arJson_bet635= json_decode( $row['bet635_data'], true );
	$arJson_live90bet= json_decode( $row['polymarket_data'], true );

	/* add odds_data json */

	## determine which to use,, in order of unibet,qrbet, then toto
	
	if(isset($row['unibet_data']) && !is_null($row['unibet_data'])) {
		// the field is not null
		$arJson = $arJson_unibet;
	} else {
		// the field is null or doesn't exist
		if(isset($row['qrbet_data']) && !is_null($row['qrbet_data'])) {
			// the field is not null
			$arJson = $arJson_qrbet;
		} else {
			// the field is null or doesn't exist
			if(isset($row['bet635_data']) && !is_null($row['bet635_data'])) {
				// the field is not null
				$arJson = $arJson_bet635;
			} else {
				// the field is null or doesn't exist
				if(isset($row['odds_data']) && !is_null($row['odds_data'])) {
					// the field is not null
					$arJson = $arJson_toto;
				} else {
					// the field is null or doesn't exist
					
				}
			}
		}
	}
	//$arJson = $arJson_toto;

	$toto_1  = $arJson_toto[$toto_market_constant_a];
	$toto_x  = $arJson_toto[$toto_market_constant_b];

	$betfair_1  = $arJson[$betfair_market_constant_a]['lay_price'];
	$betfair_x  = $arJson[$betfair_market_constant_b]['lay_price'];
//echo ">> ".$toto_1." - ".$betfair_1."<br>";
	$betfair_1_vwap = $arJson[$betfair_market_constant_a]['vwap'];
	$betfair_x_vwap = $arJson[$betfair_market_constant_b]['vwap'];

	$betfair_1v  = round($arJson[$betfair_market_constant_a]['lay_vol']/$currency_conversion_rate);
	$betfair_xv  =round( $arJson[$betfair_market_constant_b]['lay_vol']/$currency_conversion_rate);

	$betfair_1vL  =round( $arJson[$betfair_market_constant_a]['last_back_vol']/$currency_conversion_rate);
	$betfair_xvL  =round( $arJson[$betfair_market_constant_b]['last_back_vol']/$currency_conversion_rate);

	$betfair_1vT  = $arJson[$betfair_market_constant_a]['lowest_back_price'];
	$betfair_xvT  = $arJson[$betfair_market_constant_b]['lowest_back_price'];


	$unibet_1  = $arJson_unibet[$unibet_market_constant_a];
	$unibet_x  = $arJson_unibet[$unibet_market_constant_b];

	$contra_1  = $arJson_contra[$contra_market_constant_a];
	$contra_x  = $arJson_contra[$contra_market_constant_b];

	$qrbet_1  = $arJson_qrbet[$qrbet_market_constant_a];
	$qrbet_x  = $arJson_qrbet[$qrbet_market_constant_b];

	$winkel_toto_1  = $arJson_winkel_toto[$winkel_toto_market_constant_a];
	$winkel_toto_x  = $arJson_winkel_toto[$winkel_toto_market_constant_b];

	$bingoal_1  = $arJson_bingoal[$bingoal_market_constant_a];
	$bingoal_x  = $arJson_bingoal[$bingoal_market_constant_b];

	$yess365_1  = $arJson_yess365[$yess365_market_constant_a];
	$yess365_x  = $arJson_yess365[$yess365_market_constant_b];

	$betalpha_1  = $arJson_betalpha[$betalpha_market_constant_a];
	$betalpha_x  = $arJson_betalpha[$betalpha_market_constant_b];

	$bet3000_1  = $arJson_bet3000[$bet3000_market_constant_a];
	$bet3000_x  = $arJson_bet3000[$bet3000_market_constant_b];

	$m8bets_1  = $arJson_m8bets[$m8bets_market_constant_a];
	$m8bets_x  = $arJson_m8bets[$m8bets_market_constant_b];

	$bet635_1  = $arJson_bet635[$bet635_market_constant_a];
	$bet635_x  = $arJson_bet635[$bet635_market_constant_b];

	$live90bet_1  = $arJson_live90bet[$live90bet_market_constant_a];
	$live90bet_x  = $arJson_live90bet[$live90bet_market_constant_b];
	/* add 1x market */

	if ($howmanyways===3){
		$toto_2  = $arJson_toto[$toto_market_constant_c];
		
		$betfair_2  = $arJson[$betfair_market_constant_c]['lay_price'];
		//echo "toto2:".$toto_2." - betfair:".$betfair_2."<br>";
		$betfair_2v  = round($arJson[$betfair_market_constant_c]['lay_vol']/$currency_conversion_rate);

		$betfair_2_vwap = $arJson[$betfair_market_constant_c]['vwap'];

		$unibet_2  = $arJson_unibet[$unibet_market_constant_c];
		$contra_2  = $arJson_contra[$contra_market_constant_c];
		$qrbet_2  = $arJson_qrbet[$qrbet_market_constant_c];
		$winkel_toto_2  = $arJson_winkel_toto[$winkel_toto_market_constant_c];
		$bingoal_2  = $arJson_bingoal[$bingoal_market_constant_c];
		$yess365_2  = $arJson_yess365[$yess365_market_constant_c];
		$betalpha_2  = $arJson_betalpha[$betalpha_market_constant_c];
		$bet3000_2  = $arJson_bet3000[$bet3000_market_constant_c];
		$m8bets_2  = $arJson_m8bets[$m8bets_market_constant_c];
		$bet635_2  = $arJson_bet635[$bet635_market_constant_c];
		$live90bet_2  = $arJson_live90bet[$live90bet_market_constant_c];
		
		/* add second market */
		
		$betfair_2vL  = round($arJson[$betfair_market_constant_c]['last_back_vol']/$currency_conversion_rate);
		$betfair_2vT  = $arJson[$betfair_market_constant_c]['lowest_back_price'];

		if (($toto_1<$toto_2 and $betfair_1>$betfair_2 and $betfair_2>0) or ($toto_1>$toto_2 and $betfair_1<$betfair_2 and $betfair_1>0) ){
			$temp = $toto_1;
			$toto_1 = $toto_2;
			$toto_2 = $temp;
		} elseif (($betfair_2==0 and ($toto_1 - $betfair_1)/$betfair_1>0.3) or ($betfair_1==0 and ($toto_2 - $betfair_2)/$betfair_2>0.3) ){
			$temp = $toto_1;
			$toto_1 = $toto_2;
			$toto_2 = $temp;
		}

		if (($unibet_1<$unibet_2 and $betfair_1>$betfair_2 and $betfair_2>0) or ($unibet_1>$unibet_2 and $betfair_1<$betfair_2 and $betfair_1>0) ){
			$temp = $unibet_1;
			$unibet_1 = $unibet_2;
			$unibet_2 = $temp;
		} elseif (($betfair_2==0 and ($unibet_1 - $betfair_1)/$betfair_1>0.3) or ($betfair_1==0 and ($unibet_2 - $betfair_2)/$betfair_2>0.3) ){
			$temp = $unibet_1;
			$unibet_1 = $unibet_2;
			$unibet_2 = $temp;
		}

		if (($winkel_toto_1<$winkel_toto_2 and $betfair_1>$betfair_2 and $betfair_2>0) or ($winkel_toto_1>$winkel_toto_2 and $betfair_1<$betfair_2 and $betfair_1>0) ){
			$temp = $winkel_toto_1;
			$winkel_toto_1 = $winkel_toto_2;
			$winkel_toto_2 = $temp;
		} elseif (($betfair_2==0 and ($winkel_toto_1 - $betfair_1)/$betfair_1>0.3) or ($betfair_1==0 and ($winkel_toto_2 - $betfair_2)/$betfair_2>0.3) ){
			$temp = $winkel_toto_1;
			$winkel_toto_1 = $winkel_toto_2;
			$winkel_toto_2 = $temp;
		}

		if (($qrbet_1<$qrbet_2 and $betfair_1>$betfair_2 and $betfair_2>0) or ($qrbet_1>$qrbet_2 and $betfair_1<$betfair_2 and $betfair_1>0) ){
			$temp = $qrbet_1;
			$qrbet_1 = $qrbet_2;
			$qrbet_2 = $temp;
		} elseif (($betfair_2==0 and ($qrbet_1 - $betfair_1)/$betfair_1>0.3) or ($betfair_1==0 and ($qrbet_2 - $betfair_2)/$betfair_2>0.3) ){
			$temp = $qrbet_1;
			$qrbet_1 = $qrbet_2;
			$qrbet_2 = $temp;
		}
		if (($yess365_1<$yess365_2 and $betfair_1>$betfair_2 and $betfair_2>0) or ($yess365_1>$yess365_2 and $betfair_1<$betfair_2 and $betfair_1>0) ){
			$temp = $yess365_1;
			$yess365_1 = $yess365_2;
			$yess365_2 = $temp;
		} elseif (($betfair_2==0 and ($yess365_1 - $betfair_1)/$betfair_1>0.3) or ($betfair_1==0 and ($yess365_2 - $betfair_2)/$betfair_2>0.3) ){
			$temp = $yess365_1;
			$yess365_1 = $yess365_2;
			$yess365_2 = $temp;
		}

		if (($betalpha_1<$betalpha_2 and $betfair_1>$betfair_2 and $betfair_2>0) or ($betalpha_1>$betalpha_2 and $betfair_1<$betfair_2 and $betfair_1>0) ){
			$temp = $betalpha_1;
			$betalpha_1 = $betalpha_2;
			$betalpha_2 = $temp;
		} elseif (($betfair_2==0 and ($betalpha_1 - $betfair_1)/$betfair_1>0.3) or ($betfair_1==0 and ($betalpha_2 - $betfair_2)/$betfair_2>0.3) ){
			$temp = $betalpha_1;
			$betalpha_1 = $betalpha_2;
			$betalpha_2 = $temp;
		}

		if (($bet3000_1<$bet3000_2 and $betfair_1>$betfair_2 and $betfair_2>0) or ($bet3000_1>$bet3000_2 and $betfair_1<$betfair_2 and $betfair_1>0) ){
			$temp = $bet3000_1;
			$bet3000_1 = $bet3000_2;
			$bet3000_2 = $temp;
		} elseif (($betfair_2==0 and ($bet3000_1 - $betfair_1)/$betfair_1>0.3) or ($betfair_1==0 and ($bet3000_2 - $betfair_2)/$betfair_2>0.3) ){
			$temp = $bet3000_1;
			$bet3000_1 = $bet3000_2;
			$bet3000_2 = $temp;
		}


		if (($bingoal_1<$bingoal_2 and $betfair_1>$betfair_2 and $betfair_2>0) or ($bingoal_1>$bingoal_2 and $betfair_1<$betfair_2 and $betfair_1>0) ){
			$temp = $bingoal_1;
			$bingoal_1 = $bingoal_2;
			$bingoal_2 = $temp;
		} elseif (($betfair_2==0 and ($bingoal_1 - $betfair_1)/$betfair_1>0.3) or ($betfair_1==0 and ($bingoal_2 - $betfair_2)/$betfair_2>0.3) ){
			$temp = $bingoal_1;
			$bingoal_1 = $bingoal_2;
			$bingoal_2 = $temp;
		}

		if (($m8bets_1<$m8bets_2 and $betfair_1>$betfair_2 and $betfair_2>0) or ($m8bets_1>$m8bets_2 and $betfair_1<$betfair_2 and $betfair_1>0) ){
			$temp = $m8bets_1;
			$m8bets_1 = $m8bets_2;
			$m8bets_2 = $temp;
		} elseif (($betfair_2==0 and ($m8bets_1 - $betfair_1)/$betfair_1>0.3) or ($betfair_1==0 and ($m8bets_2 - $betfair_2)/$betfair_2>0.3) ){
			$temp = $m8bets_1;
			$m8bets_1 = $m8bets_2;
			$m8bets_2 = $temp;
		}

		if (($bet635_1<$bet635_2 and $betfair_1>$betfair_2 and $betfair_2>0) or ($bet635_1>$bet635_2 and $betfair_1<$betfair_2 and $betfair_1>0) ){
			$temp = $bet635_1;
			$bet635_1 = $bet635_2;
			$bet635_2 = $temp;
		} elseif (($betfair_2==0 and ($bet635_1 - $betfair_1)/$betfair_1>0.3) or ($betfair_1==0 and ($bet635_2 - $betfair_2)/$betfair_2>0.3) ){
			$temp = $bet635_1;
			$bet635_1 = $bet635_2;
			$bet635_2 = $temp;
		}

		if (($live90bet_1<$live90bet_2 and $betfair_1>$betfair_2 and $betfair_2>0) or ($live90bet_1>$live90bet_2 and $betfair_1<$betfair_2 and $betfair_1>0) ){
			$temp = $live90bet_1;
			$live90bet_1 = $live90bet_2;
			$live90bet_2 = $temp;
		} elseif (($betfair_2==0 and ($live90bet_1 - $betfair_1)/$betfair_1>0.3) or ($betfair_1==0 and ($live90bet_2 - $betfair_2)/$betfair_2>0.3) ){
			$temp = $live90bet_1;
			$live90bet_1 = $live90bet_2;
			$live90bet_2 = $temp;
		}



		/* add flip market check */

		//or ((abs(($unibet_1 - $betfair_1)/$betfair_1)+ abs(($unibet_2 - $betfair_2)/$betfair_2))>0.5) 
		/*if ((abs(($unibet_1 - $betfair_1)/$betfair_1)+ abs(($unibet_2 - $betfair_2)/$betfair_2))>0.4){
			$temp = $unibet_1;
			$unibet_1 = $unibet_2;
			$unibet_2 = $temp;
		}
		
		if (abs(($winkel_toto_1 - $betfair_1)/$betfair_1)>0.25 and abs(($winkel_toto_2 - $betfair_2)/$betfair_2)>0.25){
			$temp = $winkel_toto_1;
			$winkel_toto_1 = $winkel_toto_2;
			$winkel_toto_2 = $temp;
		}
		
		if (abs(($yess365_1 - $betfair_1)/$betfair_1)>0.25 and abs(($yess365_2 - $betfair_2)/$betfair_2)>0.25){
			$temp = $yess365_1;
			$yess365_1 = $yess365_2;
			$yess365_2 = $temp;
		}*/
		/*if ((($qrbet_1 - $betfair_1)/$betfair_1)<0.05 or (($qrbet_2 - $betfair_2)/$betfair_2)<0.05){
			$temp = $qrbet_1;
			$qrbet_1 = $qrbet_2;
			$qrbet_2 = $temp;
		}
		
		if ((($unibet_1 - $betfair_1)/$betfair_1)>0.05 or (($unibet_2 - $betfair_2)/$betfair_2)<0.05){
			$temp = $unibet_1;
			$unibet_1 = $unibet_2;
			$unibet_2 = $temp;
		}
		
		
		if ((($winkel_toto_1 - $betfair_1)/$betfair_1)<0.05 or (($winkel_toto_2 - $betfair_2)/$betfair_2)<0.05){
			$temp = $winkel_toto_1;
			$winkel_toto_1 = $winkel_toto_2;
			$winkel_toto_2 = $temp;
		}
		
		if ((($bingoal_1 - $betfair_1)/$betfair_1)<0.05 or (($bingoal_2 - $betfair_2)/$betfair_2)<0.05){
			$temp = $bingoal_1;
			$bingoal_1 = $bingoal_2;
			$bingoal_2 = $temp;
		}
		
		if ((($yess365_1 - $betfair_1)/$betfair_1)<0.05 or (($yess365_2 - $betfair_2)/$betfair_2)<0.05){
			$temp = $yess365_1;
			$yess365_1 = $yess365_2;
			$yess365_2 = $temp;
		}
		
		
		if (abs(($betalpha_1 - $betfair_1)/$betfair_1)>0.4 and abs(($betalpha_2 - $betfair_2)/$betfair_2)>0.4){
			$temp = $betalpha_1;
			$betalpha_1 = $betalpha_2;
			$betalpha_2 = $temp;
		} */
		
	} else {

		
		$betfair_2=1;
		$betfair_2v=1;
		$toto_2=0;
		$unibet_2=0;
		$contra_2=0;
		$qrbet_2=0;
		$winkel_toto_2=0;
		$bingoal_2=0;
		$yess365_2=0;
		$betalpha_2=0;
		$bet3000_2=0;
		$m8bets_2=0;
		$bet635_2=0;
		$live90bet=0;
		/* add second market zero */



		

		
	}

	//echo "**".$row[13]."**".$row[26]."**".$row[39]."**";
	//echo ">>".($row[13] | $row[26] | $row[39])."<<<br><br>";

	if (isset($row[13])){
		//echo "13 notnull".$row[13].'<br>';
		$league = $row[13];
	} else{

		if (isset($row[26])){
			//echo "26 notnull".$row[26].'<br>';
			$league = $row[26];
		}else{
			if (isset($row[39])){
				//echo "39 notnull".$row[39].'<br>';
				$league = $row[39];
			} else {
				if (isset($row[52])){
					//echo "39 notnull".$row[39].'<br>';
					$league = $row[52];
				} else {
					if (isset($row[65])){
						//echo "39 notnull".$row[39].'<br>';
						$league = $row[65];
					}
				}
			}
		}
	}
	//echo "LEAGUE:".$league."<br>";
	//$league = $row[13];
	//$tz_offet = $_SESSION['time']*3600;
	//echo '<br>'.$row[2].">>".$row[15].">>".$row[28]."<<<";
	//echo "---+".($row[2] | $row[15] | $row[28])."+---";
	//                        from here?? added flipped
	$x = ($row[2] | $row[15] | $row[29] | $row[42] | $row[55]) + $tz_offet; // < just use OR across each of the fields,,
	$timestamp = date("Y-m-d H:i:s",$x);
	//echo "TIMESTAMP:".$timestamp."<br>";
	$arr= explode(" ",$timestamp);
	$t_date = $arr[0];
	$t_time = substr($arr[1], 0,5);//;
	$matchid=$row['id'];
	$t1_toto_fuzzy =0;// $row['t1_fuzzy'];
	$t2_toto_fuzzy =0;// $row['t2_fuzzy'];
	$t1_unibet_fuzzy =0;// $row['t1_unibet_fuzzy'];
	$t2_unibet_fuzzy = 0;//$row['t2_unibet_fuzzy'];
	$t1_winkel_toto_fuzzy =0;// $row['t1_unibet_fuzzy'];
	$t2_winkel_toto_fuzzy = 0;//$row['t2_unibet_fuzzy'];
	$t1_bingoal_fuzzy =0;// $row['t1_unibet_fuzzy'];
	$t2_bingoal_fuzzy = 0;//$row['t2_unibet_fuzzy'];

	//these are teh eventids for each book,,
	$toto_event_id = $row['toto_event_id'];
	$unibet_event_id = $row['unibet_event_id'];
	$contra_event_id = $row['contra_event_id'];
	$qrbet_event_id = $row['qrbet_event_id'];
	$winkel_toto_event_id = $row['winkel_toto_event_id'];
	$bingoal_event_id = $row['bingoal_event_id'];
	$yess365_event_id = $row['yess365_event_id'];
	$betalpha_event_id = $row['betalpha_event_id'];
	$bet3000_event_id = $row['bet3000_event_id'];
	$m8bets_event_id = $row['m8bets_event_id'];
	$bet635_event_id = $row['bet635_event_id'];
	$live90bet_event_id = $row['polymarket_event_id'];
	
	/* add book event id */

	//$betfair_event_id = $row['betfair_event_id'];
	if (isset($row[4])){
		//echo "13 notnull".$row[13].'<br>';
		$betfair_event_id = $row[4];
	} else{

		if (isset($row[17])){
			//echo "26 notnull".$row[26].'<br>';
			$betfair_event_id = $row[17];
		}else{
			if (isset($row[30])){
				//echo "39 notnull".$row[39].'<br>';
				$betfair_event_id = $row[30];
			} else {
				if (isset($row[43])){
					//echo "39 notnull".$row[39].'<br>';
					$betfair_event_id = $row[43];
				} else {
					if (isset($row[56])){
						//echo "39 notnull".$row[39].'<br>';
						$betfair_event_id = $row[56];
					}
				}
			}
		}
	}
	//echo $qrbet_event_id."<br>";
	//echo "hello!!!";

	//$league = $row

	
	if (isset($row[7])){
		$betfair_team_1 = $row[7];
	} else{

		if (isset($row[20])){
			
			$betfair_team_1 = $row[20];
		}else{
			if (isset($row[33])){
				
				$betfair_team_1 = $row[33];
			} else {
				if (isset($row[46])){
				
					$betfair_team_1 = $row[46];
				}  else {
					if (isset($row[59])){
					
						$betfair_team_1 = $row[59];
					}
				}
			}
		}
	}

	if (isset($row[8])){
		$betfair_team_2 = $row[8];
	} else{

		if (isset($row[21])){
			
			$betfair_team_2 = $row[21];
		}else{
			if (isset($row[34])){
				
				$betfair_team_2 = $row[34];
			} else {
				if (isset($row[47])){
				
					$betfair_team_2 = $row[47];
				}else {
					if (isset($row[60])){
					
						$betfair_team_2 = $row[60];
					}
				}

			}
		}
	}
	//echo $betfair_team_1."-".$betfair_team_2."<>".$betfair_event_id."<br>";

	$odds_total=0;
	$book_1_count=0;
	$book_x_count=0;
	$book_2_count=0;
	$odds_1_total=0;
	$odds_x_total=0;
	$odds_2_total=0;

	if ($show_toto){
		$odds_total+=$toto_1+$toto_x;
		if ($toto_1>0){
			$book_1_count+=1;
			$odds_1_total+=$toto_1;
		}
		if ($toto_x>0){
			$book_x_count+=1;
			$odds_x_total+=$toto_x;
		}
		if ($toto_2>0){
			$book_2_count+=1;
			$odds_2_total+=$toto_2;
		}
	}
	if ($show_unibet){
		$odds_total+=$unibet_1+$unibet_x;
		if ($unibet_1>0){
			$book_1_count+=1;
			$odds_1_total+=$unibet_1;
		}
		if ($unibet_x>0){
			$book_x_count+=1;
			$odds_x_total+=$unibet_x;
		}
		if ($unibet_2>0){
			$book_2_count+=1;
			$odds_2_total+=$unibet_2;
		}
	}
	if ($show_contra){
		$odds_total+=$contra_1+$contra_x;
		if ($contra_1>0){
			$book_1_count+=1;
			$odds_1_total+=$contra_1;
		}
		if ($contra_x>0){
			$book_x_count+=1;
			$odds_x_total+=$contra_x;
		}
		if ($contra_2>0){
			$book_2_count+=1;
			$odds_2_total+=$contra_2;
		}
	}
	if ($show_qrbet){
		$odds_total+=$qrbet_1+$qrbet_x;
		if ($qrbet_1>0){
			$book_1_count+=1;
			$odds_1_total+=$qrbet_1;
		}
		if ($qrbet_x>0){
			$book_x_count+=1;
			$odds_x_total+=$qrbet_x;
		}
		if ($qrbet_2>0){
			$book_2_count+=1;
			$odds_2_total+=$qrbet_2;
		}
	}
	if ($show_winkel_toto){
		$odds_total+=$winkel_toto_1+$winkel_toto_x;
		if ($winkel_toto_1>0){
			$book_1_count+=1;
			$odds_1_total+=$winkel_toto_1;
		}
		if ($winkel_toto_x>0){
			$book_x_count+=1;
			$odds_x_total+=$winkel_toto_x;
		}
		if ($winkel_toto_2>0){
			$book_2_count+=1;
			$odds_2_total+=$winkel_toto_2;
		}
	}

	if ($show_bingoal){
		$odds_total+=$bingoal_1+$bingoal_x;
		if ($bingoal_1>0){
			$book_1_count+=1;
			$odds_1_total+=$bingoal_1;
		}
		if ($bingoal_x>0){
			$book_x_count+=1;
			$odds_x_total+=$bingoal_x;
		}
		if ($bingoal_2>0){
			$book_2_count+=1;
			$odds_2_total+=$bingoal_2;
		}
	}

	if ($show_betalpha){
		$odds_total+=$betalpha_1+$betalpha_x;
		if ($betalpha_1>0){
			$book_1_count+=1;
			$odds_1_total+=$betalpha_1;
		}
		if ($betalpha_x>0){
			$book_x_count+=1;
			$odds_x_total+=$betalpha_x;
		}
		if ($betalpha_2>0){
			$book_2_count+=1;
			$odds_2_total+=$betalpha_2;
		}
	}

	if ($show_bet3000){
		$odds_total+=$bet3000_1+$bet3000_x;
		if ($bet3000_1>0){
			$book_1_count+=1;
			$odds_1_total+=$bet3000_1;
		}
		if ($bet3000_x>0){
			$book_x_count+=1;
			$odds_x_total+=$bet3000_x;
		}
		if ($bet3000_2>0){
			$book_2_count+=1;
			$odds_2_total+=$bet3000_2;
		}
	}


	if ($show_m8bets){
		$odds_total+=$m8bets_1+$m8bets_x;
		if ($m8bets_1>0){
			$book_1_count+=1;
			$odds_1_total+=$m8bets_1;
		}
		if ($m8bets_x>0){
			$book_x_count+=1;
			$odds_x_total+=$m8bets_x;
		}
		if ($m8bets_2>0){
			$book_2_count+=1;
			$odds_2_total+=$m8bets_2;
		}
	}

	if ($show_bet635){
		$odds_total+=$bet635_1+$bet635_x;
		if ($bet635_1>0){
			$book_1_count+=1;
			$odds_1_total+=$bet635_1;
		}
		if ($bet635_x>0){
			$book_x_count+=1;
			$odds_x_total+=$bet635_x;
		}
		if ($bet635_2>0){
			$book_2_count+=1;
			$odds_2_total+=$bet635_2;
		}
	}


	if ($show_live90bet){
		$odds_total+=$live90bet_1+$live90bet_x;
		if ($live90bet_1>0){
			$book_1_count+=1;
			$odds_1_total+=$live90bet_1;
		}
		if ($live90bet_x>0){
			$book_x_count+=1;
			$odds_x_total+=$live90bet_x;
		}
		if ($live90bet_2>0){
			$book_2_count+=1;
			$odds_2_total+=$live90bet_2;
		}
	}

	/* add book total/count */

	//$odds_total=1;
	//

//	echo "odds1:".$odds_1_total."<>"."oddsx:".$odds_x_total."<>"."odds2:".$odds_2_total."<br>";

	//here i check bf_sort,, for the 1_x2, x_12, or 2_1x.. and then filter matches based on there total_matched.. of each market..

	if ($bf_sort=="bf_1_x2"){
		$bf_1_matched_min=2000;
		$bf_1_matched_max=200000000;
		$bf_x_matched_min=0;
		$bf_x_matched_max=100;
		$bf_2_matched_min=0;
		$bf_2_matched_max=100;

	}else if ($bf_sort=="bf_x_12"){
		$bf_1_matched_min=0;
		$bf_1_matched_max=100;
		$bf_x_matched_min=2000;
		$bf_x_matched_max=200000000;
		$bf_2_matched_min=0;
		$bf_2_matched_max=100;
		
	}else if ($bf_sort=="bf_2_1x"){
		$bf_1_matched_min=0;
		$bf_1_matched_max=100;
		$bf_x_matched_min=0;
		$bf_x_matched_max=100;
		$bf_2_matched_min=2000;
		$bf_2_matched_max=200000000;
		
	}else{
		$bf_1_matched_min=0;
		$bf_1_matched_max=200000000;
		$bf_x_matched_min=0;
		$bf_x_matched_max=200000000;
		$bf_2_matched_min=0;
		$bf_2_matched_max=200000000;
		
	}
	//echo $bf_sort;
	//echo $bf_1_matched_min."||".$bf_1_matched_max."<>".$betfair_1v."<br>";
	//($betfair_1v > $bf_1_matched_min and $betfair_1v < $bf_1_matched_max)  and
	//echo $betfair_team_1."<>".$betfair_team_2."|".$betfair_1vL."|".$betfair_xvL."|".$betfair_2vL."<br>";
	//  (($betfair_1vL >= $bf_1_matched_min and $betfair_1vL<=$bf_1_matched_max) and ( $betfair_xvL >= $bf_x_matched_min and $betfair_xvL<=$bf_x_matched_max) and($betfair_2vL >= $bf_2_matched_min and $betfair_2vL<=$bf_2_matched_max)) and 
	if  (($betfair_1vL >= $bf_1_matched_min and $betfair_1vL <= $bf_1_matched_max)   and ( $betfair_xvL >= $bf_x_matched_min and $betfair_xvL<=$bf_x_matched_max) and ($betfair_2vL >= $bf_2_matched_min and $betfair_2vL<=$bf_2_matched_max) and ($betfair_1>0 and $betfair_x>0  and $odds_total>0 and !(in_array($league,$ignored_comps)))){
		//echo $contra_1."<>".$contra_x."<>".$contra_2."--".$betfair_team_1."<>".$betfair_team_2."<>".$betfair_1."||".$betfair_x."||".$betfair_2."(".$odds_total.")<br>";
	//	echo "IN_A<br>";
		$all_matched_bf=0;
	//1x2
	$all_matched_bf+=$arJson['bf_1_odds']['last_back_vol'];
	$all_matched_bf+=$arJson['bf_x_odds']['last_back_vol'];
	$all_matched_bf+=$arJson['bf_2_odds']['last_back_vol'];
	//HT
	$all_matched_bf+=$arJson['bf_1_ht']['last_back_vol'];
	$all_matched_bf+=$arJson['bf_x_ht']['last_back_vol'];
	$all_matched_bf+=$arJson['bf_2_ht']['last_back_vol'];
	//uo25
	$all_matched_bf+=$arJson['bf_Under_2.5']['last_back_vol'];
	$all_matched_bf+=$arJson['bf_Over_2.5']['last_back_vol'];
	//uo35
	$all_matched_bf+=$arJson['bf_Under_3.5']['last_back_vol'];
	$all_matched_bf+=$arJson['bf_Over_3.5']['last_back_vol'];
	//dnb
	$all_matched_bf+=$arJson['bf_dnb_home']['last_back_vol'];
	$all_matched_bf+=$arJson['bf_dnb_away']['last_back_vol'];
	//dc
	$all_matched_bf+=$arJson['bf_dc_1x']['last_back_vol'];
	$all_matched_bf+=$arJson['bf_dc_12']['last_back_vol'];
	$all_matched_bf+=$arJson['bf_dc_x2']['last_back_vol'];

	$bf_market_p1 =   round($betfair_1v/$all_matched_bf,2);
	if (is_infinite($bf_market_p1)){
		$bf_market_p1 = 0;
	}
	$bf_market_p2 =  round($betfair_xv/$all_matched_bf,2);
	if (is_infinite($bf_market_p2)){
		$bf_market_p2 = 0;
	}
	$bf_market_p3 =  round($betfair_2v/$all_matched_bf,2);
	if (is_infinite($bf_market_p3)){
		$bf_market_p3 = 0;
	}
	$bf_market_p =  round(($betfair_1v + $betfair_xv + $betfair_2v)/$all_matched_bf,2);
	if (is_infinite($bf_market_p)){
		$bf_market_p = 0;
	}

	//echo $betfair_team_1."<>".$betfair_team_2."<>".$betfair_1_vwap."||".$betfair_x_vwap."||".$betfair_2_vwap."><".$betfair_1vT."||".$betfair_xvT."||".$betfair_2vT."<br>";
		
	//echo $betfair_1_vwap."^".$betfair_1vT."<br>";
	if ($betfair_1vT>0){
	$betfair_1_vwap_perc = ($betfair_1_vwap-$betfair_1vT)/$betfair_1vT;
	if ($betfair_1_vwap_perc==-1){
		$betfair_1_vwap_perc=0;
	}}else{
		$betfair_1_vwap_perc=0;
	}
	//echo $betfair_1_vwap_perc."<br>";

	//echo $betfair_x_vwap."^".$betfair_1vT."<br>";
	if ($betfair_xvT>0){
	$betfair_x_vwap_perc = ($betfair_x_vwap-$betfair_xvT)/$betfair_xvT;
	if ($betfair_x_vwap_perc==-1){
		$betfair_x_vwap_perc=0;
	}}else{
		$betfair_x_vwap_perc=0;
	}

	if ($betfair_2vT>0){
	$betfair_2_vwap_perc = ($betfair_2_vwap-$betfair_2vT)/$betfair_2vT;
	if ($betfair_2_vwap_perc==-1){
		$betfair_2_vwap_perc=0;
	}}else{
		$betfair_2_vwap_perc=0;
	}

	$betfair_max_vwap = max($betfair_1_vwap_perc,$betfair_x_vwap_perc,$betfair_2_vwap_perc);
	//echo $betfair_team_1."<>".$betfair_team_2."   ".$betfair_1."(".$betfair_1_vwap.")|".$betfair_x."(".$betfair_x_vwap.")|".$betfair_2."(".$betfair_2_vwap.")";
	if (($betfair_1>0 and $live90bet_1>$betfair_1 and $show_live90bet) or ($betfair_x>0 and $live90bet_x>$betfair_x and $show_live90bet) or ($betfair_2>0 and $live90bet_2>$betfair_2 and $show_live90bet) or ($betfair_1>0 and $bet635_1>$betfair_1 and $show_bet635) or ($betfair_x>0 and $bet635_x>$betfair_x and $show_bet635) or ($betfair_2>0 and $bet635_2>$betfair_2 and $show_bet635) or ($betfair_1>0 and $m8bets_1>$betfair_1 and $show_m8bets) or ($betfair_x>0 and $m8bets_x>$betfair_x and $show_m8bets) or ($betfair_2>0 and $m8bets_2>$betfair_2 and $show_m8bets) or ($betfair_1>0 and $yess365_1>$betfair_1 and $show_yess365) or ($betfair_x>0 and $yess365_x>$betfair_x and $show_yess365) or ($betfair_2>0 and $yess365_2>$betfair_2 and $show_yess365) or ($betfair_1>0 and $bingoal_1>$betfair_1 and $show_bingoal) or ($betfair_x>0 and $bingoal_x>$betfair_x and $show_bingoal) or ($betfair_2>0 and $bingoal_2>$betfair_2 and $show_bingoal) or ($betfair_1>0 and $winkel_toto_1>$betfair_1 and $show_winkel_toto) or ($betfair_x>0 and $winkel_toto_x>$betfair_x and $show_winkel_toto) or ($betfair_2>0 and $winkel_toto_2>$betfair_2 and $show_winkel_toto) or ($betfair_1>0 and $qrbet_1>$betfair_1 and $show_qrbet) or ($betfair_x>0 and $qrbet_x>$betfair_x and $show_qrbet) or ($betfair_2>0 and $qrbet_2>$betfair_2 and $show_qrbet) or ($betfair_1>0 and  $toto_1>$betfair_1 and $show_toto) or  ($betfair_x>0 and $toto_x>$betfair_x and $show_toto) or  ($betfair_2>0 and $toto_2>$betfair_2 and $show_toto) or  ($betfair_1>0 and $unibet_1>$betfair_1 and $show_unibet) or  ($betfair_x>0 and $unibet_x>$betfair_x and $show_unibet) or  ($betfair_2>0 and $unibet_2>$betfair_2 and $show_unibet) or  ($betfair_1>0 and $contra_1>$betfair_1 and $show_contra) or  ($betfair_x>0 and $contra_x>$betfair_x and $show_contra) or ($betfair_2>0 and $contra_2>$betfair_2 and $show_contra ) or  ($betfair_1>0 and $bet3000_1>$betfair_1 and $show_bet3000) or  ($betfair_x>0 and $bet3000_x>$betfair_x and $show_bet3000) or ($betfair_2>0 and $bet3000_2>$betfair_2 and $show_bet3000 ) or  ($betfair_1>0 and $betalpha_1>$betfair_1 and $show_betalpha) or  ($betfair_x>0 and $betalpha_x>$betfair_x and $show_betalpha) or ($betfair_2>0 and $betalpha_2>$betfair_2 and $show_betalpha )){
		/* add red sort */
		//red_matches
		//echo "red:".$contra_1."<>".$contra_x."<>".$contra_2."--".$betfair_team_1."<>".$betfair_team_2."<>".$betfair_1."||".$betfair_x."||".$betfair_2."(".$odds_total.")<br>";
		//	echo "IN_SHOW_RED:".$row['team_1_toto'].'/'.$row['team_2_toto'].'--'.$betfair_1.'-'.$betfair_x.'-'.$betfair_2."<br>";

	// here i need to add in the percentage check,, so figure out which book is the best,, and then take that percentage,,
	// thread it into the array,, and then sort on that..


	$max_1 = max($m8bets_1*$show_m8bets,$bet3000_1*$show_bet3000,$betalpha_1*$show_betalpha,$bingoal_1*$show_bingoal,$winkel_toto_1*$show_winkel_toto,$toto_1*$show_toto,$unibet_1*$show_unibet,$qrbet_1*$show_qrbet,$contra_1*$show_contra);
	$max_x = max($m8bets_x*$show_m8bets,$bet3000_x*$show_bet3000,$betalpha_x*$show_betalpha,$bingoal_x*$show_bingoal,$winkel_toto_x*$show_winkel_toto,$toto_x*$show_toto,$unibet_x*$show_unibet,$qrbet_x*$show_qrbet,$contra_x*$show_contra);
	$max_2 = max($m8bets_2*$show_m8bets,$bet3000_2*$show_bet3000,$betalpha_2*$show_betalpha,$bingoal_2*$show_bingoal,$winkel_toto_2*$show_winkel_toto,$toto_2*$show_toto,$unibet_2*$show_unibet,$qrbet_2*$show_qrbet,$contra_2*$show_contra);

	$per_1 = $max_1/$betfair_1*100-100;
	$per_x = $max_x/$betfair_x*100-100;
	$per_2 = $max_2/$betfair_2*100-100;
	$max_per = max($per_1,$per_x,$per_2);

	// here just tally up all matched amounts on betfair markets,, then take percentage of the market over whole, also i guess
	// the runner over whole..


		/* add to red matches */
		$red_matches[] = array("bf_ltp_1"=>$betfair_1vT,"bf_ltp_x"=>$betfair_xvT,"bf_ltp_2"=>$betfair_2vT,"betfair_vwap_max"=>$betfair_max_vwap,"betfair_1_vwap_perc"=>$betfair_1_vwap_perc,"betfair_x_vwap_perc"=>$betfair_x_vwap_perc,"betfair_2_vwap_perc"=>$betfair_2_vwap_perc,"betfair_1_vwap"=>$betfair_1_vwap,"betfair_x_vwap"=>$betfair_x_vwap,"betfair_2_vwap"=>$betfair_2_vwap,"bf_market_p"=>$bf_market_p,"bf_market_p1"=>$bf_market_p1,"bf_market_p2"=>$bf_market_p2,"bf_market_p3"=>$bf_market_p3,"percentage"=>$max_per,"avg_1"=>$odds_1_total/$book_1_count,"avg_x"=>$odds_x_total/$book_x_count,"avg_2"=>$odds_2_total/$book_2_count,"date"=>$t_date,"time"=>$t_time,"t1_toto"=>$row['team_1_toto'],"t2_toto"=>$row['team_2_toto'],"t1_unibet"=>$row['team_1_unibet'],"t2_unibet"=>$row['team_2_unibet'],"t1_betfair"=>$betfair_team_1,"t2_betfair"=>$betfair_team_2,"t1_toto_fuzzy"=>$t1_toto_fuzzy,"t2_toto_fuzzy"=>$t2_toto_fuzzy,"t1_unibet_fuzzy"=>$t1_unibet_fuzzy,"t2_unibet_fuzzy"=>$t2_unibet_fuzzy,"betalpha_1"=>$betalpha_1,"betalpha_x"=>$betalpha_x,"betalpha_2"=>$betalpha_2,"bingoal_1"=>$bingoal_1,"bingoal_x"=>$bingoal_x,"bingoal_2"=>$bingoal_2,"toto_1"=>$toto_1,"toto_x"=>$toto_x,"toto_2"=>$toto_2,"unibet_1"=>$unibet_1,"unibet_x"=>$unibet_x,"unibet_2"=>$unibet_2,"qrbet_1"=>$qrbet_1,"qrbet_x"=>$qrbet_x,"qrbet_2"=>$qrbet_2,"betfair_1"=>$betfair_1,"betfair_x"=>$betfair_x,"betfair_2"=>$betfair_2,"betfair_1v"=>$betfair_1v,"betfair_xv"=>$betfair_xv,"betfair_2v"=>$betfair_2v,"betfair_1vL"=>$betfair_1vL ,"betfair_xvL"=>$betfair_xvL ,"betfair_2vL"=>$betfair_2vL,  "matchid"=>$matchid,"toto_event_id"=>$toto_event_id,"bingoal_event_id"=>$bingoal_event_id,"unibet_event_id"=>$unibet_event_id,"betfair_event_id"=>$betfair_event_id,"league"=>$league,"contra_1"=>$contra_1,"contra_x"=>$contra_x,"contra_2"=>$contra_2,"winkel_toto_1"=>$winkel_toto_1,"winkel_toto_x"=>$winkel_toto_x,"winkel_toto_2"=>$winkel_toto_2,"yess365_1"=>$yess365_1,"yess365_x"=>$yess365_x,"yess365_2"=>$yess365_2,"bet3000_1"=>$bet3000_1,"bet3000_x"=>$bet3000_x,"bet3000_2"=>$bet3000_2,"yess365_event_id"=>$yess365_event_id,"contra_event_id"=>$contra_event_id,"qrbet_event_id"=>$qrbet_event_id,"winkel_toto_event_id"=>$winkel_toto_event_id,"betalpha_event_id"=>$betalpha_event_id,"bet3000_event_id"=>$bet3000_event_id,"m8bets_1"=>$m8bets_1,"m8bets_x"=>$m8bets_x,"m8bets_2"=>$m8bets_2,"bet635_1"=>$bet635_1,"bet635_x"=>$bet635_x,"bet635_2"=>$bet635_2,"live90bet_1"=>$live90bet_1,"live90bet_x"=>$live90bet_x,"live90bet_2"=>$live90bet_2,"bet635_event_id"=>$bet635_event_id,"live90bet_event_id"=>$live90bet_event_id,"m8bets_event_id"=>$m8bets_event_id,"total_matched_volume"=>$betfair_1vL+$betfair_xvL+$betfair_2vL);
	} else if (($live90bet_1>=$betfair_1-0.05 and $betfair_1>0 and $show_live90bet) or ($live90bet_x>=$betfair_x-0.05 and $betfair_x>0 and $show_live90bet) or ($live90bet_2>=$betfair_2-0.05 and $betfair_2>0 and $show_live90bet) or ($bet635_1>=$betfair_1-0.05 and $betfair_1>0 and $show_bet635) or ($bet635_x>=$betfair_x-0.05 and $betfair_x>0 and $show_bet635) or ($bet635_2>=$betfair_2-0.05 and $betfair_2>0 and $show_bet635) or ($m8bets_1>=$betfair_1-0.05 and $betfair_1>0 and $show_m8bets) or ($m8bets_x>=$betfair_x-0.05 and $betfair_x>0 and $show_m8bets) or ($m8bets_2>=$betfair_2-0.05 and $betfair_2>0 and $show_m8bets) or ($betalpha_1>=$betfair_1-0.05 and $betfair_1>0 and $show_betalpha) or ($betalpha_x>=$betfair_x-0.05 and $betfair_x>0 and $show_betalpha) or ($betalpha_2>=$betfair_2-0.05 and $betfair_2>0 and $show_betalpha) or ($bet3000_1>=$betfair_1-0.05 and $betfair_1>0 and $show_bet3000) or ($bet3000_x>=$betfair_x-0.05 and $betfair_x>0 and $show_bet3000) or ($bet3000_2>=$betfair_2-0.05 and $betfair_2>0 and $show_bet3000) or  ($yess365_1>=$betfair_1-0.05 and $betfair_1>0 and $show_yess365) or ($yess365_x>=$betfair_x-0.05 and $betfair_x>0 and $show_yess365) or ($yess365_2>=$betfair_2-0.05 and $betfair_2>0 and $show_yess365) or ($bingoal_1>=$betfair_1-0.05 and $betfair_1>0 and $show_bingoal) or ($bingoal_x>=$betfair_x-0.05 and $betfair_x>0 and $show_bingoal) or ($bingoal_2>=$betfair_2-0.05 and $betfair_2>0 and $show_bingoal) or ($winkel_toto_1>=$betfair_1-0.05 and $betfair_1>0 and $show_winkel_toto) or ($winkel_toto_x>=$betfair_x-0.05 and $betfair_x>0 and $show_winkel_toto) or ($winkel_toto_2>=$betfair_2-0.05 and $betfair_2>0 and $show_winkel_toto) or ($qrbet_1>=$betfair_1-0.05 and $betfair_1>0 and $show_qrbet) or ($qrbet_x>=$betfair_x-0.05 and $betfair_x>0 and $show_qrbet) or ($qrbet_2>=$betfair_2-0.05 and $betfair_2>0 and $show_qrbet) or ($toto_1>=$betfair_1-0.05 and $betfair_1>0 and $show_toto) or ($toto_x>=$betfair_x-0.05 and $betfair_x>0 and $show_toto) or ($toto_2>=$betfair_2-0.05 and $betfair_2>0 and $show_toto) or ($unibet_1>=$betfair_1-0.05 and $betfair_1>0 and $show_unibet) or ($unibet_x>=$betfair_x-0.05 and $betfair_x>0 and $show_unibet)  or ($unibet_2>=$betfair_2-0.05 and $betfair_2>0 and $show_unibet) or ($contra_1>=$betfair_1-0.05 and $betfair_1>0 and $show_contra) or ($contra_x>=$betfair_x-0.05 and $betfair_x>0 and $show_contra)  or ($contra_2>=$betfair_2-0.05 and $betfair_2>0 and $show_contra)){
		//green matches
		/* add green sort */
		//echo "green:".$toto_1."<>".$toto_x."<>".$toto_2."--".$betfair_team_1."<>".$betfair_team_2."<>".$betfair_1."||".$betfair_x."||".$betfair_2."(".$odds_total.")<br><br>";
	$max_1=0;
	if ($winkel_toto_1>=$betfair_1-0.05 and $betfair_1>0 and $winkel_toto_1>$max_1){
		$max_1=$winkel_toto_1*$show_winkel_toto;
	}
	if ($toto_1>=$betfair_1-0.05 and $betfair_1>0 and $toto_1>$max_1){
		$max_1=$toto_1*$show_toto;
	}if ($unibet_1>=$betfair_1-0.05 and $betfair_1>0 and $unibet_1>$max_1){
		$max_1=$unibet_1*$show_unibet;
	}if ($contra_1>=$betfair_1-0.05 and $betfair_1>0 and $contra_1>$max_1){
		$max_1=$contra_1*$show_contra;
	}if ($qrbet_1>=$betfair_1-0.05 and $betfair_1>0 and $qrbet_1>$max_1){
		$max_1=$qrbet_1*$show_qrbet;
	}if ($bingoal_1>=$betfair_1-0.05 and $betfair_1>0 and $bingoal_1>$max_1){
		$max_1=$bingoal_1*$show_bingoal;
	}if ($betalpha_1>=$betfair_1-0.05 and $betfair_1>0 and $betalpha_1>$max_1){
		$max_1=$betalpha_1*$show_betalpha;
	}if ($bet3000_1>=$betfair_1-0.05 and $betfair_1>0 and $bet3000_1>$max_1){
		$max_1=$bet3000_1*$show_bet3000;
	}if ($bet635_1>=$betfair_1-0.05 and $betfair_1>0 and $bet635_1>$max_1){
		$max_1=$bet635_1*$show_bet635;
	}if ($live90bet_1>=$betfair_1-0.05 and $betfair_1>0 and $live90bet_1>$max_1){
		$max_1=$live90bet_1*$show_live90bet;
	}


	$max_x=0;
	if ($winkel_toto_x>=$betfair_x-0.05 and $betfair_x>0 and $winkel_toto_x>$max_x){
		$max_x=$winkel_toto_x*$show_winkel_toto;
	}
	if ($toto_x>=$betfair_x-0.05 and $betfair_x>0 and $toto_x>$max_x){
		$max_x=$toto_x*$show_toto;
	}if ($unibet_x>=$betfair_x-0.05 and $betfair_x>0 and $unibet_x>$max_x){
		$max_x=$unibet_x*$show_unibet;
	}if ($contra_x>=$betfair_x-0.05 and $betfair_x>0 and $contra_x>$max_x){
		$max_x=$contra_x*$show_contra;
	}if ($qrbet_x>=$betfair_x-0.05 and $betfair_x>0 and $qrbet_x>$max_x){
		$max_x=$qrbet_x*$show_qrbet;
	}if ($bingoal_x>=$betfair_x-0.05 and $betfair_x>0 and $bingoal_x>$max_x){
		$max_x=$bingoal_x*$show_bingoal;
	}if ($betalpha_x>=$betfair_x-0.05 and $betfair_x>0 and $betalpha_x>$max_x){
		$max_x=$betalpha_x*$show_betalpha;
	}if ($bet3000_x>=$betfair_x-0.05 and $betfair_x>0 and $bet3000_x>$max_x){
		$max_x=$bet3000_x*$show_bet3000;
	}if ($bet635_x>=$betfair_x-0.05 and $betfair_x>0 and $bet635_x>$max_x){
		$max_x=$bet635_x*$show_bet635;
	}if ($live90bet_x>=$betfair_x-0.05 and $betfair_x>0 and $live90bet_x>$max_x){
		$max_x=$live90bet_x*$show_live90bet;
	}

	$max_2=0;
	if ($winkel_toto_2>=$betfair_2-0.05 and $betfair_2>0 and $winkel_toto_2>$max_2){
		$max_2=$winkel_toto_2*$show_winkel_toto;
	}
	if ($toto_2>=$betfair_2-0.05 and $betfair_2>0 and $toto_2>$max_2){
		$max_2=$toto_2*$show_toto;
	}if ($unibet_2>=$betfair_2-0.05 and $betfair_2>0 and $unibet_2>$max_2){
		$max_2=$unibet_2*$show_unibet;
	}if ($contra_2>=$betfair_2-0.05 and $betfair_2>0 and $contra_2>$max_2){
		$max_2=$contra_2*$show_contra;
	}if ($qrbet_2>=$betfair_2-0.05 and $betfair_2>0 and $qrbet_2>$max_2){
		$max_2=$qrbet_2*$show_qrbet;
	}if ($bingoal_2>=$betfair_2-0.05 and $betfair_2>0 and $bingoal_2>$max_2){
		$max_2=$bingoal_2*$show_bingoal;
	}if ($betalpha_2>=$betfair_2-0.05 and $betfair_2>0 and $betalpha_2>$max_2){
		$max_2=$betalpha_2*$show_betalpha;
	}if ($bet3000_2>=$betfair_2-0.05 and $betfair_2>0 and $bet3000_2>$max_2){
		$max_2=$bet3000_2*$show_bet3000;
	}if ($bet635_1>=$betfair_1-0.05 and $betfair_1>0 and $bet635_1>$max_1){
		$max_1=$bet635_1*$show_bet635;
	}if ($live90bet_1>=$betfair_1-0.05 and $betfair_1>0 and $live90bet_1>$max_1){
		$max_1=$live90bet_1*$show_live90bet;
	}if ($bet635_2>=$betfair_2-0.05 and $betfair_2>0 and $bet635_2>$max_2){
		$max_2=$bet635_2*$show_bet635;
	}if ($live90bet_2>=$betfair_2-0.05 and $betfair_2>0 and $live90bet_2>$max_2){
		$max_2=$live90bet_2*$show_live90bet;
	}

	$per_1 = round($max_1/$betfair_1*100-100,2);
	$per_x =round( $max_x/$betfair_x*100-100,2);
	$per_2 = round($max_2/$betfair_2*100-100,2);
	if (is_nan($per_1)){
		$per_1=-100;
	}else{

	}
	if (is_nan($per_x)){
		$per_x=-100;
	}
	if (is_nan($per_2)){
		$per_2=-100;
	}

	$max_per = max($per_1,$per_x,$per_2);
	//echo  $betfair_team_1." >> ".$max_per." >> ".$per_1." | ".$per_x." | ".$per_2." <<";
	/* add to green matches */
		$green_matches[] = array("bf_ltp_1"=>$betfair_1vT,"bf_ltp_x"=>$betfair_xvT,"bf_ltp_2"=>$betfair_2vT,"betfair_vwap_max"=>$betfair_max_vwap,"betfair_1_vwap_perc"=>$betfair_1_vwap_perc,"betfair_x_vwap_perc"=>$betfair_x_vwap_perc,"betfair_2_vwap_perc"=>$betfair_2_vwap_perc,"betfair_1_vwap"=>$betfair_1_vwap,"betfair_x_vwap"=>$betfair_x_vwap,"betfair_2_vwap"=>$betfair_2_vwap,"betalpha_1"=>$betalpha_1,"betalpha_x"=>$betalpha_x,"betalpha_2"=>$betalpha_2,"bf_market_p"=>$bf_market_p,"bf_market_p1"=>$bf_market_p1,"bf_market_p2"=>$bf_market_p2,"bf_market_p3"=>$bf_market_p3,"percentage"=>$max_per,"avg_1"=>$odds_1_total/$book_1_count,"avg_x"=>$odds_x_total/$book_x_count,"avg_2"=>$odds_2_total/$book_2_count,"date"=>$t_date,"time"=>$t_time,"t1_toto"=>$row['team_1_toto'],"t2_toto"=>$row['team_2_toto'],"t1_unibet"=>$row['team_1_unibet'],"t2_unibet"=>$row['team_2_unibet'],"t1_betfair"=>$betfair_team_1,"t2_betfair"=>$betfair_team_2,"t1_toto_fuzzy"=>$t1_toto_fuzzy,"t2_toto_fuzzy"=>$t2_toto_fuzzy,"t1_unibet_fuzzy"=>$t1_unibet_fuzzy,"t2_unibet_fuzzy"=>$t2_unibet_fuzzy,"bingoal_1"=>$bingoal_1,"bingoal_x"=>$bingoal_x,"bingoal_2"=>$bingoal_2,"toto_1"=>$toto_1,"toto_x"=>$toto_x,"toto_2"=>$toto_2,"unibet_1"=>$unibet_1,"unibet_x"=>$unibet_x,"unibet_2"=>$unibet_2,"qrbet_1"=>$qrbet_1,"qrbet_x"=>$qrbet_x,"qrbet_2"=>$qrbet_2,"betfair_1"=>$betfair_1,"betfair_x"=>$betfair_x,"betfair_2"=>$betfair_2,"betfair_1v"=>$betfair_1v,"betfair_xv"=>$betfair_xv,"betfair_2v"=>$betfair_2v,"betfair_1vL"=>$betfair_1vL ,"betfair_xvL"=>$betfair_xvL ,"betfair_2vL"=>$betfair_2vL, "matchid"=>$matchid,"toto_event_id"=>$toto_event_id,"unibet_event_id"=>$unibet_event_id,"bingoal_event_id"=>$bingoal_event_id,"betfair_event_id"=>$betfair_event_id,"league"=>$league,"contra_1"=>$contra_1,"contra_x"=>$contra_x,"contra_2"=>$contra_2,"yess365_1"=>$yess365_1,"yess365_x"=>$yess365_x,"yess365_2"=>$yess365_2,"yess365_event_id"=>$yess365_event_id,"winkel_toto_1"=>$winkel_toto_1,"winkel_toto_x"=>$winkel_toto_x,"winkel_toto_2"=>$winkel_toto_2,"bet3000_1"=>$bet3000_1,"bet3000_x"=>$bet3000_x,"bet3000_2"=>$bet3000_2,"contra_event_id"=>$contra_event_id,"qrbet_event_id"=>$qrbet_event_id,"winkel_toto_event_id"=>$winkel_toto_event_id,"betalpha_event_id"=>$betalpha_event_id,"bet3000_event_id"=>$bet3000_event_id,"m8bets_1"=>$m8bets_1,"m8bets_x"=>$m8bets_x,"m8bets_2"=>$m8bets_2,"m8bets_event_id"=>$m8bets_event_id,"bet635_1"=>$bet635_1,"bet635_x"=>$bet635_x,"bet635_2"=>$bet635_2,"live90bet_1"=>$live90bet_1,"live90bet_x"=>$live90bet_x,"live90bet_2"=>$live90bet_2,"bet635_event_id"=>$bet635_event_id,"live90bet_event_id"=>$live90bet_event_id,"total_matched_volume"=>$betfair_1vL+$betfair_xvL+$betfair_2vL);
	} else {
		//regular_matches
	//	echo "regs:".$contra_1."<>".$contra_x."<>".$contra_2."--".$betfair_team_1."<>".$betfair_team_2."<>".$betfair_1."||".$betfair_x."||".$betfair_2."(".$odds_total.")<br>";
		/* add to regular matches */
		$regular_matches[] = array("bf_ltp_1"=>$betfair_1vT,"bf_ltp_x"=>$betfair_xvT,"bf_ltp_2"=>$betfair_2vT,"betfair_vwap_max"=>$betfair_max_vwap,"betfair_1_vwap_perc"=>$betfair_1_vwap_perc,"betfair_x_vwap_perc"=>$betfair_x_vwap_perc,"betfair_2_vwap_perc"=>$betfair_2_vwap_perc,"betfair_1_vwap"=>$betfair_1_vwap,"betfair_x_vwap"=>$betfair_x_vwap,"betfair_2_vwap"=>$betfair_2_vwap,"betalpha_1"=>$betalpha_1,"betalpha_x"=>$betalpha_x,"betalpha_2"=>$betalpha_2,"bf_market_p"=>$bf_market_p,"bf_market_p1"=>$bf_market_p1,"bf_market_p2"=>$bf_market_p2,"bf_market_p3"=>$bf_market_p3,"percentage"=>0,"avg_1"=>$odds_1_total/$book_1_count,"avg_x"=>$odds_x_total/$book_x_count,"avg_2"=>$odds_2_total/$book_2_count,"date"=>$t_date,"time"=>$t_time,"t1_toto"=>$row['team_1_toto'],"t2_toto"=>$row['team_2_toto'],"t1_unibet"=>$row['team_1_unibet'],"t2_unibet"=>$row['team_2_unibet'],"t1_betfair"=>$betfair_team_1,"t2_betfair"=>$betfair_team_2,"t1_toto_fuzzy"=>$t1_toto_fuzzy,"t2_toto_fuzzy"=>$t2_toto_fuzzy,"t1_unibet_fuzzy"=>$t1_unibet_fuzzy,"t2_unibet_fuzzy"=>$t2_unibet_fuzzy,"bingoal_1"=>$bingoal_1,"bingoal_x"=>$bingoal_x,"bingoal_2"=>$bingoal_2,"toto_1"=>$toto_1,"toto_x"=>$toto_x,"toto_2"=>$toto_2,"unibet_1"=>$unibet_1,"unibet_x"=>$unibet_x,"unibet_2"=>$unibet_2,"qrbet_1"=>$qrbet_1,"qrbet_x"=>$qrbet_x,"qrbet_2"=>$qrbet_2,"betfair_1"=>$betfair_1,"betfair_x"=>$betfair_x,"betfair_2"=>$betfair_2,"betfair_1v"=>$betfair_1v,"betfair_xv"=>$betfair_xv,"betfair_2v"=>$betfair_2v,"betfair_1vL"=>$betfair_1vL ,"betfair_xvL"=>$betfair_xvL ,"betfair_2vL"=>$betfair_2vL, "matchid"=>$matchid,"toto_event_id"=>$toto_event_id,"unibet_event_id"=>$unibet_event_id,"bingoal_event_id"=>$bingoal_event_id,"betfair_event_id"=>$betfair_event_id,"league"=>$league,"contra_1"=>$contra_1,"contra_x"=>$contra_x,"contra_2"=>$contra_2,"yess365_1"=>$yess365_1,"yess365_x"=>$yess365_x,"yess365_2"=>$yess365_2,"yess365_event_id"=>$yess365_event_id,"winkel_toto_1"=>$winkel_toto_1,"winkel_toto_x"=>$winkel_toto_x,"winkel_toto_2"=>$winkel_toto_2,"bet3000_1"=>$bet3000_1,"bet3000_x"=>$bet3000_x,"bet3000_2"=>$bet3000_2,"contra_event_id"=>$contra_event_id,"qrbet_event_id"=>$qrbet_event_id,"winkel_toto_event_id"=>$winkel_toto_event_id,"betalpha_event_id"=>$betalpha_event_id,"bet3000_event_id"=>$bet3000_event_id,"m8bets_1"=>$m8bets_1,"m8bets_x"=>$m8bets_x,"m8bets_2"=>$m8bets_2,"m8bets_event_id"=>$m8bets_event_id,"bet635_1"=>$bet635_1,"bet635_x"=>$bet635_x,"bet635_2"=>$bet635_2,"live90bet_1"=>$live90bet_1,"live90bet_x"=>$live90bet_x,"live90bet_2"=>$live90bet_2,"bet635_event_id"=>$bet635_event_id,"live90bet_event_id"=>$live90bet_event_id,"total_matched_volume"=>$betfair_1vL+$betfair_xvL+$betfair_2vL);
	}
	}
}

$end_time = microtime(true);
$elapsed_time = $end_time - $start_time;
//echo "<br>LoopA took " . $elapsed_time . " seconds to execute.";


$start_time = microtime(true);

$sortitem=$bf_sort;//$params["bfsort"];


 if ($sortitem==="1"){
		$sortitem = "betfair_1v";
	} else if ($sortitem==="x") { 
 		$sortitem = "betfair_xv";
	} else if ($sortitem==="2"){
		if ($market==="dnb"){
            $sortitem = "betfair_xv";
		}else{
		    $sortitem = "betfair_2v";
		}
	} else if ($sortitem==="u") { 
			$sortitem = "betfair_1v";
	}  else if ($sortitem==="o") { 
		$sortitem = "betfair_xv";
    } else {
		if ($sortitem==="nada"){
			$sortitem="nada";
		}else{
			//leave it.
		}
	}

	//echo "sorting by:".$sortitem;

if ($sortitem==="nada"){
	//no sort
	$sort_filter = array_column($red_matches, "percentage");//$sortitem );
array_multisort($sort_filter, SORT_DESC, $red_matches);

$sort_filter = array_column($green_matches,"percentage");//, $sortitem );
array_multisort($sort_filter, SORT_DESC, $green_matches);

$sort_filter = array_column($regular_matches,"date");//
array_multisort($sort_filter, SORT_ASC, $regular_matches);
}else if ($sortitem=="1x_tm"){
	echo ">>".$sortitem."<<";
 $sort_filter = array_column($red_matches, "total_matched_volume");//$sortitem );
array_multisort($sort_filter, SORT_DESC, $red_matches);

$sort_filter = array_column($green_matches,"total_matched_volume");//, $sortitem );
array_multisort($sort_filter, SORT_DESC, $green_matches);


$sort_filter = array_column($regular_matches,"total_matched_volume");//$sortitem );
array_multisort($sort_filter, SORT_DESC, $regular_matches);
} else if ($sortitem=="vwap_1_asc"){
echo ">>".$sortitem."<<";
$sort_filter = array_column($red_matches, "betfair_1_vwap_perc");//$sortitem );
array_multisort($sort_filter, SORT_ASC, $red_matches);

$sort_filter = array_column($green_matches,"betfair_1_vwap_perc");//, $sortitem );
array_multisort($sort_filter, SORT_ASC, $green_matches);


$sort_filter = array_column($regular_matches,"betfair_1_vwap_perc");//$sortitem );
array_multisort($sort_filter, SORT_ASC, $regular_matches);

} else if ($sortitem=="vwap_asc"){

	echo ">^>".$sortitem."<<";

	$all_matches = $red_matches + $green_matches + $regular_matches;
	$sort_filter = array_column($all_matches, "betfair_vwap_max");//$sortitem );
	array_multisort($sort_filter, SORT_ASC, $all_matches);

	$red_matches = $all_matches;
	$green_matches=array();
	$regular_matches=array();

	//echo var_dump($red_matches);
	/*$sort_filter = array_column($red_matches, "betfair_vwap_max");//$sortitem );
	array_multisort($sort_filter, SORT_ASC, $red_matches);
	
	$sort_filter = array_column($green_matches,"betfair_vwap_max");//, $sortitem );
	array_multisort($sort_filter, SORT_ASC, $green_matches);
	
	
	$sort_filter = array_column($regular_matches,"betfair_vwap_max");//$sortitem );
	array_multisort($sort_filter, SORT_ASC, $regular_matches);*/

}
else if ($sortitem=="vwap_desc"){

//	echo ">!>".$sortitem."<< >>";

	$all_matches =array_merge($red_matches, $green_matches, $regular_matches);
	$sort_filter = array_column($all_matches, "betfair_vwap_max");//$sortitem );
	array_multisort($sort_filter, SORT_DESC, $all_matches);

	$red_matches = $all_matches;

	$green_matches=array();
	$regular_matches=array();
	
	/*
	$sort_filter = array_column($red_matches, "betfair_vwap_max");//$sortitem );
	array_multisort($sort_filter, SORT_DESC, $red_matches);
	
	$sort_filter = array_column($green_matches,"betfair_vwap_max");//, $sortitem );
	array_multisort($sort_filter, SORT_DESC, $green_matches);
	
	
	$sort_filter = array_column($regular_matches,"betfair_vwap_max");//$sortitem );
	array_multisort($sort_filter, SORT_DESC, $regular_matches);*/
}
else if ($sortitem=="vwap_1_desc"){

	//echo ">>".$sortitem."<<";
	$sort_filter = array_column($red_matches, "betfair_1_vwap_perc");//$sortitem );
	array_multisort($sort_filter, SORT_DESC, $red_matches);
	
	$sort_filter = array_column($green_matches,"betfair_1_vwap_perc");//, $sortitem );
	array_multisort($sort_filter, SORT_DESC, $green_matches);
	
	
	$sort_filter = array_column($regular_matches,"betfair_1_vwap_perc");//$sortitem );
	array_multisort($sort_filter, SORT_DESC, $regular_matches);
} else if ($sortitem=="vwap_x_asc"){
	echo ">>".$sortitem."<<";
	$sort_filter = array_column($red_matches, "betfair_x_vwap_perc");//$sortitem );
	array_multisort($sort_filter, SORT_ASC, $red_matches);
	
	$sort_filter = array_column($green_matches,"betfair_x_vwap_perc");//, $sortitem );
	array_multisort($sort_filter, SORT_ASC, $green_matches);
	
	
	$sort_filter = array_column($regular_matches,"betfair_x_vwap_perc");//$sortitem );
	array_multisort($sort_filter, SORT_ASC, $regular_matches);
	
	} else if ($sortitem=="vwap_x_desc"){
	
		//echo ">>".$sortitem."<<";
		$sort_filter = array_column($red_matches, "betfair_x_vwap_perc");//$sortitem );
		array_multisort($sort_filter, SORT_DESC, $red_matches);
		
		$sort_filter = array_column($green_matches,"betfair_x_vwap_perc");//, $sortitem );
		array_multisort($sort_filter, SORT_DESC, $green_matches);
		
		
		$sort_filter = array_column($regular_matches,"betfair_x_vwap_perc");//$sortitem );
		array_multisort($sort_filter, SORT_DESC, $regular_matches);
	} else if ($sortitem=="vwap_2_asc"){
		echo ">>".$sortitem."<<";
		$sort_filter = array_column($red_matches, "betfair_2_vwap_perc");//$sortitem );
		array_multisort($sort_filter, SORT_ASC, $red_matches);
		
		$sort_filter = array_column($green_matches,"betfair_2_vwap_perc");//, $sortitem );
		array_multisort($sort_filter, SORT_ASC, $green_matches);
		
		
		$sort_filter = array_column($regular_matches,"betfair_2_vwap_perc");//$sortitem );
		array_multisort($sort_filter, SORT_ASC, $regular_matches);
		
		} else if ($sortitem=="vwap_2_desc"){
		
			//echo ">>".$sortitem."<<";
			$sort_filter = array_column($red_matches, "betfair_2_vwap_perc");//$sortitem );
			array_multisort($sort_filter, SORT_DESC, $red_matches);
			
			$sort_filter = array_column($green_matches,"betfair_2_vwap_perc");//, $sortitem );
			array_multisort($sort_filter, SORT_DESC, $green_matches);
			
			
			$sort_filter = array_column($regular_matches,"betfair_2_vwap_perc");//$sortitem );
			array_multisort($sort_filter, SORT_DESC, $regular_matches);
		} else if ($sortitem=="12_tm"){
//	echo ">>".$sortitem."<<";

	$sort_filter = array_column($red_matches, "betfair_2vL");//$sortitem );
	array_multisort($sort_filter, SORT_DESC, $red_matches);
	
	$sort_filter = array_column($green_matches,"betfair_2vL");//, $sortitem );
	array_multisort($sort_filter, SORT_DESC, $green_matches);
	
	
	$sort_filter = array_column($regular_matches,"betfair_2vL");//$sortitem );
	array_multisort($sort_filter, SORT_DESC, $regular_matches);
}else if ($sortitem=="x2_tm"){
//	echo ">>".$sortitem."<<";
	$sort_filter = array_column($red_matches, "betfair_xvL");//$sortitem );
	array_multisort($sort_filter, SORT_DESC, $red_matches);
	
	$sort_filter = array_column($green_matches,"betfair_xvL");//, $sortitem );
	array_multisort($sort_filter, SORT_DESC, $green_matches);
	
	
	$sort_filter = array_column($regular_matches,"betfair_xvL");//$sortitem );
	array_multisort($sort_filter, SORT_DESC, $regular_matches);
}
//now here write them out to table red > green > regular
//


$end_time = microtime(true);
$elapsed_time = $end_time - $start_time;
//echo "<br>Sorting took " . $elapsed_time . " seconds to execute.";


echo '<table id="main_table"  width=100% border=1><thead>';
//echo '<tr><th style="width:3%;background-color:white" ></th><th style="width:8%;background-color:white">date</th><th style="width:2%;background-color:white">time</th><th style=";background-color:white">league</th><th style=";background-color:white">team 1</th><th style=";background-color:white">team 2</th>';
echo '<tr><th style="width:3%" ></th><th style="width:4%">date</th><th style="width:2%">time</th><th>league</th><th>team 1</th><th>team 2</th>';


//TOTO ODDS HEADERS

if ($show_toto==="1"){
	echo '<th style="width:5%" class="normal_toto">toto_'.$header_a.'</th><th style="width:5%" class="normal_toto">toto_'.$header_b.'</th>';
	if ($howmanyways===3){
		echo '<th style="width:5%" class="normal_toto">toto_'.$header_c.'</th>';
	}
}



//CONTRA ODDS HEADERS
if ($show_contra==="1"){
echo '<th style="width:5%" class="normal_contra">cont_'.$header_a.'</th><th style="width:5%" class="normal_contra">cont_'.$header_b.'</th>';

if ($howmanyways===3){
	echo '<th style="width:5%" class="normal_contra">cont_'.$header_c.'</th>';
}
}

//QRBET ODDS HEADERS
if ($show_qrbet==="1"){
	echo '<th style="width:5%" class="normal_qrbet">qrb_'.$header_a.'</th><th style="width:5%" class="normal_qrbet">qrb_'.$header_b.'</th>';
	
if ($howmanyways===3){
		echo '<th style="width:5%" class="normal_qrbet">qrb_'.$header_c.'</th>';
	}
}
	

//WINKEL_TOTO ODDS HEADERS
if ($show_winkel_toto==="1"){
	echo '<th style="width:5%" class="normal_winkel_toto">winkto_'.$header_a.'</th><th style="width:5%"  class="normal_winkel_toto">winkto_'.$header_b.'</th>';
	
if ($howmanyways===3){
		echo '<th style="width:5%"  class="normal_winkel_toto">winkto_'.$header_c.'</th>';
	}
}

//bingoal ODDS HEADERS
if ($show_bingoal==="1"){
	echo '<th style="width:5%" class="normal_bingoal">bingoal_'.$header_a.'</th><th style="width:5%" class="normal_bingoal">bingoal_'.$header_b.'</th>';
	
if ($howmanyways===3){
		echo '<th style="width:5%" class="normal_bingoal">bingoal_'.$header_c.'</th>';
	}
}


//yess365 ODDS HEADERS
if ($show_yess365==="1"){
	echo '<th style="width:5%" class="normal_yess365">bet365_'.$header_a.'</th><th style="width:5%" class="normal_yess365">bet365_'.$header_b.'</th>';
	
if ($howmanyways===3){
		echo '<th style="width:5%" class="normal_yess365">bet365_'.$header_c.'</th>';
	}
}

//betalpha ODDS HEADERS
if ($show_betalpha==="1"){
	echo '<th style="width:5%" class="normal_betalpha">betalpha_'.$header_a.'</th><th style="width:5%" class="normal_betalpha">betalpha_'.$header_b.'</th>';
	
if ($howmanyways===3){
		echo '<th style="width:5%" class="normal_betalpha">betalpha_'.$header_c.'</th>';
	}
}



//bet3000 ODDS HEADERS
if ($show_bet3000==="1"){
	echo '<th style="width:5%" class="normal_bet3000">bet3000_'.$header_a.'</th><th style="width:5%" class="normal_bet3000">bet3000_'.$header_b.'</th>';
	
if ($howmanyways===3){
		echo '<th style="width:5%" class="normal_bet3000">bet3000_'.$header_c.'</th>';
	}
}


//m8bets ODDS HEADERS
if ($show_m8bets==="1"){
	echo '<th style="width:5%" class="normal_m8bets">m8bets_'.$header_a.'</th><th style="width:5%" class="normal_m8bets">m8bets_'.$header_b.'</th>';
	
if ($howmanyways===3){
		echo '<th style="width:5%" class="normal_m8bets">m8bets_'.$header_c.'</th>';
	}
}


//bet635 ODDS HEADERS
if ($show_bet635==="1"){
	echo '<th style="width:5%" class="normal_bet635">bet635_'.$header_a.'</th><th style="width:5%" class="normal_bet635">bet635_'.$header_b.'</th>';
	
if ($howmanyways===3){
		echo '<th style="width:5%" class="normal_bet635">bet635_'.$header_c.'</th>';
	}
}

//live90bet ODDS HEADERS
if ($show_live90bet==="1"){
	echo '<th style="width:5%" class="normal_live90bet">Polymarket '.$header_a.'</th><th style="width:5%" class="normal_live90bet">Polymarket '.$header_b.'</th>';
	
if ($howmanyways===3){
		echo '<th style="width:5%" class="normal_live90bet">Polymarket '.$header_c.'</th>';
	}
}


/* add table headers */

//avg book prices..

if ($show_avg==="1"){
	echo '<th style="width:5%" class="normal_avg">avg_'.$header_a.'</th><th style="width:5%"  class="normal_avg">avg_'.$header_b.'</th>';
		
	if ($howmanyways===3){
			echo '<th style="width:5%" class="normal_avg">avg_'.$header_c.'</th>';
		}
}



//end avg



//UNIBET ODDS HEADERS
if ($show_unibet==="1"){
	echo '<th style="width:5%" class="normal_unibet">ub_'.$header_a.'</th><th style="width:5%" class="normal_unibet">ub_'.$header_b.'</th>';
	
	if ($howmanyways===3){
		echo '<th style="width:5%" class="normal_unibet">ub_'.$header_c.'</th>';
	}
	}

echo '<th style="width:5%" class="normal_betfair">betf_'.$header_a.'</th><th style="width:5%" class="normal_betfair">betf_'.$header_b.'</th>';

if ($howmanyways===3){
	echo '<th style="width:5%" class="normal_betfair">betf_'.$header_c.'</th>';
}
echo '</tr></thead>';

//echo "reds:".count($red_matches)."<br>";
//echo "greens:".count($green_matches)."<br>";
//echo "regs:".count($regular_matches)."<br>";


$end_time = microtime(true);
$elapsed_time = $end_time - $start_time;
//echo "<br>Sorting took " . $elapsed_time . " seconds to execute.";


$start_time = microtime(true);

foreach (array($red_matches,$green_matches,$regular_matches) as $matches){
foreach ($matches as $value) {
	
	echo '<tr style="display:none">';
	//match icons
	echo '<td></td>';
	//match date time
	echo '<td class="cold">'.$value["date"].'</td><td  class="cold" style="padding:10px">'.$value["time"].'</td>';
	
	echo '<td>'.$value["league"].'</td>';

	//bf teams
	echo '<td class="cold">'.$value["t1_betfair"].'</td>';
	echo '<td class="cold">'.$value["t2_betfair"].'</td>';
	

	//TOTO ODDS
	if ($show_toto==="1"){
	//toto1
	$home_toggle = 0;

	$p = round($value['toto_1']/$value['betfair_1']*100-100,1);
	
	if ( $p<-99 or $value['betfair_1']<1){
		$p="";
	} else {
		$p = " (".$p."%)";
	}
	if ($value['toto_1']==0){
		$value['toto_1']="";
		
	}
	if ($value["toto_1"]>$value["betfair_1"] and $value['betfair_1']>0) {
		echo '<td class="red" onclick="showno(this,event'.",'".$value["toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoTotoEvent('.$value["toto_event_id"].')">'.$value["toto_1"].$p.'</td>';
		$home_toggle = 1;
	} else if ($value["toto_1"]>=$value["betfair_1"]-0.05 and $value['betfair_1']>0){
			echo '<td class="green" onclick="showno(this,event'.",'".$value["toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoTotoEvent('.$value["toto_event_id"].')">'.$value["toto_1"].$p.'</td>';
		$home_toggle = 1;
	}  else {
		echo '<td class="normal_toto" onclick="showno(this,event'.",'".$value["toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoTotoEvent('.$value["toto_event_id"].')">'.$value["toto_1"].$p.'</td>';
	}
	//totox
	$x_toggle=0;

	$p = round($value['toto_x']/$value['betfair_x']*100-100,1);
	if ( $p<-99 or $value['betfair_x']<1){
		$p="";
	} else {
		$p = " (".$p."%)";
	}
	if ($value['toto_x']==0){
		$value['toto_x']="";
		
	}
	if ($value["toto_x"]>$value["betfair_x"] and $value['betfair_x']>0) {
		echo '<td class="red" onclick="showno(this,event'.",'".$value["toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoTotoEvent('.$value["toto_event_id"].')">'.$value["toto_x"].$p.'</td>';
		$x_toggle=1;
	} else if ($value["toto_x"]>=$value["betfair_x"]-0.05 and $value['betfair_x']>0){
			echo '<td class="green" onclick="showno(this,event'.",'".$value["toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoTotoEvent('.$value["toto_event_id"].')">'.$value["toto_x"].$p.'</td>';
			$x_toggle=1;
	}  else {
		echo '<td class="normal_toto" onclick="showno(this,event'.",'".$value["toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoTotoEvent('.$value["toto_event_id"].')">'.$value["toto_x"].$p.'</td>';
	}
	//toto2

	if ($howmanyways===3){
	$away_toggle=0;

	$p = round($value['toto_2']/$value['betfair_2']*100-100,1);
	if ( $p<-99 or $value['betfair_2']<1){
		$p="";
	} else {
		$p = " (".$p."%)";
	}
	if ($value['toto_2']==0){
		$value['toto_2']="";
		
	}
	if ($value["toto_2"]>$value["betfair_2"] and $value['betfair_2']>0) {
		echo '<td class="red" onclick="showno(this,event'.",'".$value["toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoTotoEvent('.$value["toto_event_id"].')">'.$value["toto_2"].$p.'</td>';
		$away_toggle=1;
	} else if ($value["toto_2"]>=$value["betfair_2"]-0.05 and $value['betfair_2']>0){
			echo '<td class="green" onclick="showno(this,event'.",'".$value["toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoTotoEvent('.$value["toto_event_id"].')">'.$value["toto_2"].$p.'</td>';
			$away_toggle=1;
	}  else {
		echo '<td class="normal_toto" onclick="showno(this,event'.",'".$value["toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoTotoEvent('.$value["toto_event_id"].')">'.$value["toto_2"].$p.'</td>';
	}
	}
	} else { $home_toggle=0;$x_toggle=0;$away_toggle=0;
	}

	

	//CONTRA ODDS
	if ($show_contra==="1"){

	//1
	$p = round($value['contra_1']/$value['betfair_1']*100-100,1);
	if ( $p<-99 or $value['betfair_1']<1){
		$p="";
	} else {
		$p = " (".$p."%)";
	}
	if ($value['contra_1']==0){
		$value['contra_1']="";

	}
	if ($value["contra_1"]>$value["betfair_1"] and $value['betfair_1']>0) {
		echo '<td class="red" onclick="showno(this,event'.",'".$value["contra_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoContraEvent('.$value["contra_event_id"].')">'.$value["contra_1"].$p.'</td>';
		$home_toggle = 1;
	} else if ($value["contra_1"]>=$value["betfair_1"]-0.05 and $value['betfair_1']>0){
			echo '<td class="green" onclick="showno(this,event'.",'".$value["contra_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoContraEvent('.$value["contra_event_id"].')">'.$value["contra_1"].$p.'</td>';
		$home_toggle = 1;
	}  else {
		echo '<td class="normal_contra" onclick="showno(this,event'.",'".$value["contra_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoContraEvent('.$value["contra_event_id"].')">'.$value["contra_1"].$p.'</td>';
	}

	//x
	$p = round($value['contra_x']/$value['betfair_x']*100-100,1);
	if ( $p<-99 or $value['betfair_x']<1){
		$p="";
	} else {
		$p = " (".$p."%)";
	}
	if ($value['contra_x']==0){
		$value['contra_x']="";

	}
	if ($value["contra_x"]>$value["betfair_x"] and $value['betfair_x']>0) {
		echo '<td class="red" onclick="showno(this,event'.",'".$value["contra_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoContraEvent('.$value["contra_event_id"].')">'.$value["contra_x"].$p.'</td>';
		$x_toggle = 1;
	} else if ($value["contra_x"]>=$value["betfair_x"]-0.05 and $value['betfair_x']>0){
			echo '<td class="green" onclick="showno(this,event'.",'".$value["contra_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoContraEvent('.$value["contra_event_id"].')">'.$value["contra_x"].$p.'</td>';
		$x_toggle = 1;
	}  else {
		echo '<td class="normal_contra" onclick="showno(this,event'.",'".$value["contra_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoContraEvent('.$value["contra_event_id"].')">'.$value["contra_x"].$p.'</td>';
	}

	//2
	if ($howmanyways===3){
		$p = round($value['contra_2']/$value['betfair_2']*100-100,1);
		if ( $p<-99 or $value['betfair_2']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
		}
		if ($value['contra_2']==0){
			$value['contra_2']="";
	
		}
	if ($value["contra_2"]>$value["betfair_2"] and $value['betfair_2']>0) {
		echo '<td class="red" onclick="showno(this,event'.",'".$value["contra_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoContraEvent('.$value["contra_event_id"].')">'.$value["contra_2"].$p.'</td>';
$away_toggle = 1;
	} else if ($value["contra_2"]>=$value["betfair_2"]-0.05 and $value['betfair_2']>0){
			echo '<td class="green" onclick="showno(this,event'.",'".$value["contra_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoContraEvent('.$value["contra_event_id"].')">'.$value["contra_2"].$p.'</td>';
$away_toggle = 1;
	}  else {
		echo '<td class="normal_contra" onclick="showno(this,event'.",'".$value["contra_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoContraEvent('.$value["contra_event_id"].')">'.$value["contra_2"].$p.'</td>';
	}
	}
        } else { $home_toggle=0;$x_toggle=0;$away_toggle=0;
	}
	//end contra


	//QRBET ODDS
	if ($show_qrbet==="1"){

		//1
		$p = round($value['qrbet_1']/$value['betfair_1']*100-100,1);
		if ( $p<-99 or $value['betfair_1']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['qrbet_1']==0){
			$value['qrbet_1']="";
	
		}
		if ($value["qrbet_1"]>$value["betfair_1"] and $value['betfair_1']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["qrbet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoQrbetEvent('.$value["qrbet_event_id"].')">'.$value["qrbet_1"].$p.'</td>';
			$home_toggle = 1;
		} else if ($value["qrbet_1"]>=$value["betfair_1"]-0.05 and $value['betfair_1']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["qrbet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoQrbetEvent('.$value["qrbet_event_id"].')">'.$value["qrbet_1"].$p.'</td>';
			$home_toggle = 1;
		}  else {
			echo '<td class="normal_qrbet" onclick="showno(this,event'.",'".$value["qrbet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoQrbetEvent('.$value["qrbet_event_id"].')">'.$value["qrbet_1"].$p.'</td>';
		}
	
		//x
		$p = round($value['qrbet_x']/$value['betfair_x']*100-100,1);
		if ( $p<-99 or $value['betfair_x']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['qrbet_x']==0){
			$value['qrbet_x']="";
	
		}
		if ($value["qrbet_x"]>$value["betfair_x"] and $value['betfair_x']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["qrbet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoQrbetEvent('.$value["qrbet_event_id"].')">'.$value["qrbet_x"].$p.'</td>';
			$x_toggle = 1;
		} else if ($value["qrbet_x"]>=$value["betfair_x"]-0.05 and $value['betfair_x']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["qrbet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoQrbetEvent('.$value["qrbet_event_id"].')">'.$value["qrbet_x"].$p.'</td>';
			$x_toggle = 1;
		}  else {
			echo '<td class="normal_qrbet" onclick="showno(this,event'.",'".$value["qrbet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoQrbetEvent('.$value["qrbet_event_id"].')">'.$value["qrbet_x"].$p.'</td>';
		}
	
		//2
		if ($howmanyways===3){
			$p = round($value['qrbet_2']/$value['betfair_2']*100-100,1);
			if ( $p<-99 or $value['betfair_2']<1){
				$p="";
			} else {
				$p = " (".$p."%)";
			//	$p = str_replace("(%)", "", $p);
			}
			if ($value['qrbet_2']==0){
				$value['qrbet_2']="";
		
			}
		if ($value["qrbet_2"]>$value["betfair_2"] and $value['betfair_2']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["qrbet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoQrbetEvent('.$value["qrbet_event_id"].')">'.$value["qrbet_2"].$p.'</td>';
	$away_toggle = 1;
		} else if ($value["qrbet_2"]>=$value["betfair_2"]-0.05 and $value['betfair_2']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["qrbet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoQrbetEvent('.$value["qrbet_event_id"].')">'.$value["qrbet_2"].$p.'</td>';
	$away_toggle = 1;
		}  else {
			echo '<td class="normal_qrbet" onclick="showno(this,event'.",'".$value["qrbet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoQrbetEvent('.$value["qrbet_event_id"].')">'.$value["qrbet_2"].$p.'</td>';
		}
		}
			} else { $home_toggle=0;$x_toggle=0;$away_toggle=0;
		}
		//end QRBET

		//winkto ODDS
	if ($show_winkel_toto==="1"){

		//1
		$p = round($value['winkel_toto_1']/$value['betfair_1']*100-100,1);
		if ( $p<-99 or $value['betfair_1']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['winkel_toto_1']==0){
			$value['winkel_toto_1']="";
	
		}
		if ($value["winkel_toto_1"]>$value["betfair_1"] and $value['betfair_1']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["winkel_toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotowinktoEvent('."'".$value["winkel_toto_event_id"]."'".')">'.$value["winkel_toto_1"].$p.'</td>';
			$home_toggle = 1;
		} else if ($value["winkel_toto_1"]>=$value["betfair_1"]-0.05 and $value['betfair_1']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["winkel_toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotowinktoEvent('."'".$value["winkel_toto_event_id"]."'".')">'.$value["winkel_toto_1"].$p.'</td>';
			$home_toggle = 1;
		}  else {
			echo '<td class="normal_winkel_toto" onclick="showno(this,event'.",'".$value["winkel_toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotowinktoEvent('."'".$value["winkel_toto_event_id"]."'".')">'.$value["winkel_toto_1"].$p.'</td>';
		}
	
		//x
		$p = round($value['winkel_toto_x']/$value['betfair_x']*100-100,1);
		if ( $p<-99 or $value['betfair_x']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['winkel_toto_x']==0){
			$value['winkel_toto_x']="";
	
		}
		if ($value["winkel_toto_x"]>$value["betfair_x"] and $value['betfair_x']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["winkel_toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotowinktoEvent('."'".$value["winkel_toto_event_id"]."'".')">'.$value["winkel_toto_x"].$p.'</td>';
			$x_toggle = 1;
		} else if ($value["winkel_toto_x"]>=$value["betfair_x"]-0.05 and $value['betfair_x']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["winkel_toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotowinktoEvent('."'".$value["winkel_toto_event_id"]."'".')">'.$value["winkel_toto_x"].$p.'</td>';
			$x_toggle = 1;
		}  else {
			echo '<td class="normal_winkel_toto" onclick="showno(this,event'.",'".$value["winkel_toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotowinktoEvent('."'".$value["winkel_toto_event_id"]."'".')">'.$value["winkel_toto_x"].$p.'</td>';
		}
	
		//2
		if ($howmanyways===3){
			$p = round($value['winkel_toto_2']/$value['betfair_2']*100-100,1);
			if ( $p<-99 or $value['betfair_2']<1){
				$p="";
			} else {
				$p = " (".$p."%)";
			//	$p = str_replace("(%)", "", $p);
			}
			if ($value['winkel_toto_2']==0){
				$value['winkel_toto_2']="";
		
			}
		if ($value["winkel_toto_2"]>$value["betfair_2"] and $value['betfair_2']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["winkel_toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotowinktoEvent('."'".$value["winkel_toto_event_id"]."'".')">'.$value["winkel_toto_2"].$p.'</td>';
	$away_toggle = 1;
		} else if ($value["winkel_toto_2"]>=$value["betfair_2"]-0.05 and $value['betfair_2']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["winkel_toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotowinktoEvent('."'".$value["winkel_toto_event_id"]."'".')">'.$value["winkel_toto_2"].$p.'</td>';
	$away_toggle = 1;
		}  else {
			echo '<td class="normal_winkel_toto" onclick="showno(this,event'.",'".$value["winkel_toto_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotowinktoEvent('."'".$value["winkel_toto_event_id"]."'".')">'.$value["winkel_toto_2"].$p.'</td>';
		}
		}
			} else { $home_toggle=0;$x_toggle=0;$away_toggle=0;
		}
		//end winkto

		//bingoal ODDS
	if ($show_bingoal==="1"){

		//1
		$p = round($value['bingoal_1']/$value['betfair_1']*100-100,1);
		if ( $p<-99 or $value['betfair_1']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['bingoal_1']==0){
			$value['bingoal_1']="";
	
		}
		if ($value["bingoal_1"]>$value["betfair_1"] and $value['betfair_1']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["bingoal_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotobingoalEvent('."'".$value["bingoal_event_id"]."'".')">'.$value["bingoal_1"].$p.'</td>';
			$home_toggle = 1;
		} else if ($value["bingoal_1"]>=$value["betfair_1"]-0.05 and $value['betfair_1']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["bingoal_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotobingoalEvent('."'".$value["bingoal_event_id"]."'".')">'.$value["bingoal_1"].$p.'</td>';
			$home_toggle = 1;
		}  else {
			echo '<td class="normal_bingoal" onclick="showno(this,event'.",'".$value["bingoal_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotobingoalEvent('."'".$value["bingoal_event_id"]."'".')">'.$value["bingoal_1"].$p.'</td>';
		}
	
		//x
		$p = round($value['bingoal_x']/$value['betfair_x']*100-100,1);
		if ( $p<-99 or $value['betfair_x']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['bingoal_x']==0){
			$value['bingoal_x']="";
	
		}
		if ($value["bingoal_x"]>$value["betfair_x"] and $value['betfair_x']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["bingoal_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotobingoalEvent('."'".$value["bingoal_event_id"]."'".')">'.$value["bingoal_x"].$p.'</td>';
			$x_toggle = 1;
		} else if ($value["winkel_toto_x"]>=$value["betfair_x"]-0.05 and $value['betfair_x']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["bingoal_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotobingoalEvent('."'".$value["bingoal_event_id"]."'".')">'.$value["bingoal_x"].$p.'</td>';
			$x_toggle = 1;
		}  else {
			echo '<td class="normal_bingoal" onclick="showno(this,event'.",'".$value["bingoal_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotobingoalEvent('."'".$value["bingoal_event_id"]."'".')">'.$value["bingoal_x"].$p.'</td>';
		}
	
		//2
		if ($howmanyways===3){
			$p = round($value['bingoal_2']/$value['betfair_2']*100-100,1);
			if ( $p<-99 or $value['betfair_2']<1){
				$p="";
			} else {
				$p = " (".$p."%)";
			//	$p = str_replace("(%)", "", $p);
			}
			if ($value['bingoal_2']==0){
				$value['bingoal_2']="";
		
			}
		if ($value["bingoal_2"]>$value["betfair_2"] and $value['betfair_2']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["bingoal_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotobingoalEvent('."'".$value["bingoal_event_id"]."'".')">'.$value["bingoal_2"].$p.'</td>';
	$away_toggle = 1;
		} else if ($value["bingoal_2"]>=$value["betfair_2"]-0.05 and $value['betfair_2']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["bingoal_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotobingoalEvent('."'".$value["bingoal_event_id"]."'".')">'.$value["bingoal_2"].$p.'</td>';
	$away_toggle = 1;
		}  else {
			echo '<td class="normal_bingoal" onclick="showno(this,event'.",'".$value["bingoal_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotobingoalEvent('."'".$value["bingoal_event_id"]."'".')">'.$value["bingoal_2"].$p.'</td>';
		}
		}
			} else { $home_toggle=0;$x_toggle=0;$away_toggle=0;
		}
		//end bingoal


		//yess365 ODDS
	if ($show_yess365==="1"){

		//1
		$p = round($value['yess365_1']/$value['betfair_1']*100-100,1);
		if ( $p<-99 or $value['betfair_1']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['yess365_1']==0){
			$value['yess365_1']="";
	
		}
		if ($value["yess365_1"]>$value["betfair_1"] and $value['betfair_1']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["yess365_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoyess365Event('."'".$value["yess365_event_id"]."'".')">'.$value["yess365_1"].$p.'</td>';
			$home_toggle = 1;
		} else if ($value["yess365_1"]>=$value["betfair_1"]-0.05 and $value['betfair_1']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["yess365_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoyess365Event('."'".$value["yess365_event_id"]."'".')">'.$value["yess365_1"].$p.'</td>';
			$home_toggle = 1;
		}  else {
			echo '<td class="normal_yess365" onclick="showno(this,event'.",'".$value["yess365_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoyess365Event('."'".$value["yess365_event_id"]."'".')">'.$value["yess365_1"].$p.'</td>';
		}
	
		//x
		$p = round($value['yess365_x']/$value['betfair_x']*100-100,1);
		if ( $p<-99 or $value['betfair_x']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['yess365_x']==0){
			$value['yess365_x']="";
	
		}
		if ($value["yess365_x"]>$value["betfair_x"] and $value['betfair_x']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["yess365_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoyess365Event('."'".$value["yess365_event_id"]."'".')">'.$value["yess365_x"].$p.'</td>';
			$x_toggle = 1;
		} else if ($value["winkel_toto_x"]>=$value["betfair_x"]-0.05 and $value['betfair_x']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["yess365_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoyess365Event('."'".$value["yess365_event_id"]."'".')">'.$value["yess365_x"].$p.'</td>';
			$x_toggle = 1;
		}  else {
			echo '<td class="normal_yess365" onclick="showno(this,event'.",'".$value["yess365_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoyess365Event('."'".$value["yess365_event_id"]."'".')">'.$value["yess365_x"].$p.'</td>';
		}
	
		//2
		if ($howmanyways===3){
			$p = round($value['yess365_2']/$value['betfair_2']*100-100,1);
			if ( $p<-99 or $value['betfair_2']<1){
				$p="";
			} else {
				$p = " (".$p."%)";
			//	$p = str_replace("(%)", "", $p);
			}
			if ($value['yess365_2']==0){
				$value['yess365_2']="";
		
			}
		if ($value["yess365_2"]>$value["betfair_2"] and $value['betfair_2']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["yess365_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoyess365Event('."'".$value["yess365_event_id"]."'".')">'.$value["yess365_2"].$p.'</td>';
	$away_toggle = 1;
		} else if ($value["yess365_2"]>=$value["betfair_2"]-0.05 and $value['betfair_2']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["yess365_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoyess365Event('."'".$value["yess365_event_id"]."'".')">'.$value["yess365_2"].$p.'</td>';
	$away_toggle = 1;
		}  else {
			echo '<td class="normal_yess365" onclick="showno(this,event'.",'".$value["yess365_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoyess365Event('."'".$value["yess365_event_id"]."'".')">'.$value["yess365_2"].$p.'</td>';
		}
		}
			} else { $home_toggle=0;$x_toggle=0;$away_toggle=0;
		}
		//end yess365


		//betalpha ODDS
	if ($show_betalpha==="1"){

		//1
		$p = round($value['betalpha_1']/$value['betfair_1']*100-100,1);
		if ( $p<-99 or $value['betfair_1']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['betalpha_1']==0){
			$value['betalpha_1']="";
	
		}
		if ($value["betalpha_1"]>$value["betfair_1"] and $value['betfair_1']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["betalpha_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotobetalphaEvent('."'".$value["betalpha_event_id"]."'".')">'.$value["betalpha_1"].$p.'</td>';
			$home_toggle = 1;
		} else if ($value["betalpha_1"]>=$value["betfair_1"]-0.05 and $value['betfair_1']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["betalpha_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotobetalphaEvent('."'".$value["betalpha_event_id"]."'".')">'.$value["betalpha_1"].$p.'</td>';
			$home_toggle = 1;
		}  else {
			echo '<td class="normal_betalpha" onclick="showno(this,event'.",'".$value["betalpha_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotobetalphaEvent('."'".$value["betalpha_event_id"]."'".')">'.$value["betalpha_1"].$p.'</td>';
		}
	
		//x
		$p = round($value['betalpha_x']/$value['betfair_x']*100-100,1);
		if ( $p<-99 or $value['betfair_x']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['betalpha_x']==0){
			$value['betalpha_x']="";
	
		}
		if ($value["betalpha_x"]>$value["betfair_x"] and $value['betfair_x']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["betalpha_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotobetalphaEvent('."'".$value["betalpha_event_id"]."'".')">'.$value["betalpha_x"].$p.'</td>';
			$x_toggle = 1;
		} else if ($value["winkel_toto_x"]>=$value["betfair_x"]-0.05 and $value['betfair_x']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["betalpha_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotobetalphaEvent('."'".$value["betalpha_event_id"]."'".')">'.$value["betalpha_x"].$p.'</td>';
			$x_toggle = 1;
		}  else {
			echo '<td class="normal_betalpha" onclick="showno(this,event'.",'".$value["betalpha_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotobetalphaEvent('."'".$value["betalpha_event_id"]."'".')">'.$value["betalpha_x"].$p.'</td>';
		}
	
		//2
		if ($howmanyways===3){
			$p = round($value['betalpha_2']/$value['betfair_2']*100-100,1);
			if ( $p<-99 or $value['betfair_2']<1){
				$p="";
			} else {
				$p = " (".$p."%)";
			//	$p = str_replace("(%)", "", $p);
			}
			if ($value['betalpha_2']==0){
				$value['betalpha_2']="";
		
			}
		if ($value["betalpha_2"]>$value["betfair_2"] and $value['betfair_2']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["betalpha_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotobetalphaEvent('."'".$value["betalpha_event_id"]."'".')">'.$value["betalpha_2"].$p.'</td>';
	$away_toggle = 1;
		} else if ($value["betalpha_2"]>=$value["betfair_2"]-0.05 and $value['betfair_2']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["betalpha_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotobetalphaEvent('."'".$value["betalpha_event_id"]."'".')">'.$value["betalpha_2"].$p.'</td>';
	$away_toggle = 1;
		}  else {
			echo '<td class="normal_betalpha" onclick="showno(this,event'.",'".$value["betalpha_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotobetalphaEvent('."'".$value["betalpha_event_id"]."'".')">'.$value["betalpha_2"].$p.'</td>';
		}
		}
			} else { $home_toggle=0;$x_toggle=0;$away_toggle=0;
		}
		//end betalpha

		//bet3000 ODDS
	if ($show_bet3000==="1"){

		//1
		$p = round($value['bet3000_1']/$value['betfair_1']*100-100,1);
		if ( $p<-99 or $value['betfair_1']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['bet3000_1']==0){
			$value['bet3000_1']="";
	
		}
		if ($value["bet3000_1"]>$value["betfair_1"] and $value['betfair_1']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["bet3000_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotobet3000Event('."'".$value["bet3000_event_id"]."'".')">'.$value["bet3000_1"].$p.'</td>';
			$home_toggle = 1;
		} else if ($value["bet3000_1"]>=$value["betfair_1"]-0.05 and $value['betfair_1']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["bet3000_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotobet3000Event('."'".$value["bet3000_event_id"]."'".')">'.$value["bet3000_1"].$p.'</td>';
			$home_toggle = 1;
		}  else {
			echo '<td class="normal_bet3000" onclick="showno(this,event'.",'".$value["bet3000_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotobet3000Event('."'".$value["bet3000_event_id"]."'".')">'.$value["bet3000_1"].$p.'</td>';
		}
	
		//x
		$p = round($value['bet3000_x']/$value['betfair_x']*100-100,1);
		if ( $p<-99 or $value['betfair_x']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['bet3000_x']==0){
			$value['bet3000_x']="";
	
		}
		if ($value["bet3000_x"]>$value["betfair_x"] and $value['betfair_x']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["bet3000_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotobet3000Event('."'".$value["bet3000_event_id"]."'".')">'.$value["bet3000_x"].$p.'</td>';
			$x_toggle = 1;
		} else if ($value["winkel_toto_x"]>=$value["betfair_x"]-0.05 and $value['betfair_x']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["bet3000_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotobet3000Event('."'".$value["bet3000_event_id"]."'".')">'.$value["bet3000_x"].$p.'</td>';
			$x_toggle = 1;
		}  else {
			echo '<td class="normal_bet3000" onclick="showno(this,event'.",'".$value["bet3000_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotobet3000Event('."'".$value["bet3000_event_id"]."'".')">'.$value["bet3000_x"].$p.'</td>';
		}
	
		//2
		if ($howmanyways===3){
			$p = round($value['bet3000_2']/$value['betfair_2']*100-100,1);
			if ( $p<-99 or $value['betfair_2']<1){
				$p="";
			} else {
				$p = " (".$p."%)";
			//	$p = str_replace("(%)", "", $p);
			}
			if ($value['bet3000_2']==0){
				$value['bet3000_2']="";
		
			}
		if ($value["bet3000_2"]>$value["betfair_2"] and $value['betfair_2']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["bet3000_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotobet3000Event('."'".$value["bet3000_event_id"]."'".')">'.$value["bet3000_2"].$p.'</td>';
	$away_toggle = 1;
		} else if ($value["bet3000_2"]>=$value["betfair_2"]-0.05 and $value['betfair_2']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["bet3000_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotobet3000Event('."'".$value["bet3000_event_id"]."'".')">'.$value["bet3000_2"].$p.'</td>';
	$away_toggle = 1;
		}  else {
			echo '<td class="normal_bet3000" onclick="showno(this,event'.",'".$value["bet3000_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotobet3000Event('."'".$value["bet3000_event_id"]."'".')">'.$value["bet3000_2"].$p.'</td>';
		}
		}
			} else { $home_toggle=0;$x_toggle=0;$away_toggle=0;
		}
		//end bet3000


		//m8bets ODDS
	if ($show_m8bets==="1"){

		//1
		$p = round($value['m8bets_1']/$value['betfair_1']*100-100,1);
		if ( $p<-99 or $value['betfair_1']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['m8bets_1']==0){
			$value['m8bets_1']="";
	
		}
		if ($value["m8bets_1"]>$value["betfair_1"] and $value['betfair_1']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["m8bets_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotom8betsEvent('."'".$value["m8bets_event_id"]."'".')">'.$value["m8bets_1"].$p.'</td>';
			$home_toggle = 1;
		} else if ($value["m8bets_1"]>=$value["betfair_1"]-0.05 and $value['betfair_1']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["m8bets_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotom8betsEvent('."'".$value["m8bets_event_id"]."'".')">'.$value["m8bets_1"].$p.'</td>';
			$home_toggle = 1;
		}  else {
			echo '<td class="normal_m8bets" onclick="showno(this,event'.",'".$value["m8bets_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotom8betsEvent('."'".$value["m8bets_event_id"]."'".')">'.$value["m8bets_1"].$p.'</td>';
		}
	
		//x
		$p = round($value['m8bets_x']/$value['betfair_x']*100-100,1);
		if ( $p<-99 or $value['betfair_x']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['m8bets_x']==0){
			$value['m8bets_x']="";
	
		}
		if ($value["m8bets_x"]>$value["betfair_x"] and $value['betfair_x']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["m8bets_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotom8betsEvent('."'".$value["m8bets_event_id"]."'".')">'.$value["m8bets_x"].$p.'</td>';
			$x_toggle = 1;
		} else if ($value["winkel_toto_x"]>=$value["betfair_x"]-0.05 and $value['betfair_x']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["m8bets_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotom8betsEvent('."'".$value["m8bets_event_id"]."'".')">'.$value["m8bets_x"].$p.'</td>';
			$x_toggle = 1;
		}  else {
			echo '<td class="normal_m8bets" onclick="showno(this,event'.",'".$value["m8bets_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotom8betsEvent('."'".$value["m8bets_event_id"]."'".')">'.$value["m8bets_x"].$p.'</td>';
		}
	
		//2
		if ($howmanyways===3){
			$p = round($value['m8bets_2']/$value['betfair_2']*100-100,1);
			if ( $p<-99 or $value['betfair_2']<1){
				$p="";
			} else {
				$p = " (".$p."%)";
			//	$p = str_replace("(%)", "", $p);
			}
			if ($value['m8bets_2']==0){
				$value['m8bets_2']="";
		
			}
		if ($value["m8bets_2"]>$value["betfair_2"] and $value['betfair_2']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["m8bets_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotom8betsEvent('."'".$value["m8bets_event_id"]."'".')">'.$value["m8bets_2"].$p.'</td>';
	$away_toggle = 1;
		} else if ($value["m8bets_2"]>=$value["betfair_2"]-0.05 and $value['betfair_2']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["m8bets_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotom8betsEvent('."'".$value["m8bets_event_id"]."'".')">'.$value["m8bets_2"].$p.'</td>';
	$away_toggle = 1;
		}  else {
			echo '<td class="normal_m8bets" onclick="showno(this,event'.",'".$value["m8bets_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotom8betsEvent('."'".$value["m8bets_event_id"]."'".')">'.$value["m8bets_2"].$p.'</td>';
		}
		}
			} else { $home_toggle=0;$x_toggle=0;$away_toggle=0;
		}
		
		//end m8bets

		//bet635 ODDS
	if ($show_bet635==="1"){

		//1
		$p = round($value['bet635_1']/$value['betfair_1']*100-100,1);
		if ( $p<-99 or $value['betfair_1']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['bet635_1']==0){
			$value['bet635_1']="";
	
		}
		if ($value["bet635_1"]>$value["betfair_1"] and $value['betfair_1']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["bet635_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotobet635Event('."'".$value["bet635_event_id"]."'".')">'.$value["bet635_1"].$p.'</td>';
			$home_toggle = 1;
		} else if ($value["bet635_1"]>=$value["betfair_1"]-0.05 and $value['betfair_1']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["bet635_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotobet635Event('."'".$value["bet635_event_id"]."'".')">'.$value["bet635_1"].$p.'</td>';
			$home_toggle = 1;
		}  else {
			echo '<td class="normal_bet635" onclick="showno(this,event'.",'".$value["bet635_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotobet635Event('."'".$value["bet635_event_id"]."'".')">'.$value["bet635_1"].$p.'</td>';
		}
	
		//x
		$p = round($value['bet635_x']/$value['betfair_x']*100-100,1);
		if ( $p<-99 or $value['betfair_x']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['bet635_x']==0){
			$value['bet635_x']="";
	
		}
		if ($value["bet635_x"]>$value["betfair_x"] and $value['betfair_x']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["bet635_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotobet635Event('."'".$value["bet635_event_id"]."'".')">'.$value["bet635_x"].$p.'</td>';
			$x_toggle = 1;
		} else if ($value["winkel_toto_x"]>=$value["betfair_x"]-0.05 and $value['betfair_x']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["bet635_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotobet635Event('."'".$value["bet635_event_id"]."'".')">'.$value["bet635_x"].$p.'</td>';
			$x_toggle = 1;
		}  else {
			echo '<td class="normal_bet635" onclick="showno(this,event'.",'".$value["bet635_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotobet635Event('."'".$value["bet635_event_id"]."'".')">'.$value["bet635_x"].$p.'</td>';
		}
	
		//2
		if ($howmanyways===3){
			$p = round($value['bet635_2']/$value['betfair_2']*100-100,1);
			if ( $p<-99 or $value['betfair_2']<1){
				$p="";
			} else {
				$p = " (".$p."%)";
			//	$p = str_replace("(%)", "", $p);
			}
			if ($value['bet635_2']==0){
				$value['bet635_2']="";
		
			}
		if ($value["bet635_2"]>$value["betfair_2"] and $value['betfair_2']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["bet635_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotobet635Event('."'".$value["bet635_event_id"]."'".')">'.$value["bet635_2"].$p.'</td>';
	$away_toggle = 1;
		} else if ($value["bet635_2"]>=$value["betfair_2"]-0.05 and $value['betfair_2']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["bet635_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotobet635Event('."'".$value["bet635_event_id"]."'".')">'.$value["bet635_2"].$p.'</td>';
	$away_toggle = 1;
		}  else {
			echo '<td class="normal_bet635" onclick="showno(this,event'.",'".$value["bet635_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotobet635Event('."'".$value["bet635_event_id"]."'".')">'.$value["bet635_2"].$p.'</td>';
		}
		}
			} else { $home_toggle=0;$x_toggle=0;$away_toggle=0;
		}
		
		//end bet635


		//live90bet ODDS
	if ($show_live90bet==="1"){

		//1
		$p = round($value['live90bet_1']/$value['betfair_1']*100-100,1);
		if ( $p<-99 or $value['betfair_1']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['live90bet_1']==0){
			$value['live90bet_1']="";
	
		}
		$display_live90bet_1 = $value['live90bet_1'] === "" ? "" : number_format((float)$value['live90bet_1'], 2, '.', '');
		if ($value["live90bet_1"]>$value["betfair_1"] and $value['betfair_1']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["live90bet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotolive90betEvent('."'".$value["live90bet_event_id"]."'".')">'.$display_live90bet_1.$p.'</td>';
			$home_toggle = 1;
		} else if ($value["live90bet_1"]>=$value["betfair_1"]-0.05 and $value['betfair_1']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["live90bet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotolive90betEvent('."'".$value["live90bet_event_id"]."'".')">'.$display_live90bet_1.$p.'</td>';
			$home_toggle = 1;
		}  else {
			echo '<td class="normal_live90bet" onclick="showno(this,event'.",'".$value["live90bet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotolive90betEvent('."'".$value["live90bet_event_id"]."'".')">'.$display_live90bet_1.$p.'</td>';
		}
	
		//x
		$p = round($value['live90bet_x']/$value['betfair_x']*100-100,1);
		if ( $p<-99 or $value['betfair_x']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
			//$p = str_replace("(%)", "", $p);
		}
		if ($value['live90bet_x']==0){
			$value['live90bet_x']="";
	
		}
		$display_live90bet_x = $value['live90bet_x'] === "" ? "" : number_format((float)$value['live90bet_x'], 2, '.', '');
		if ($value["live90bet_x"]>$value["betfair_x"] and $value['betfair_x']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["live90bet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotolive90betEvent('."'".$value["live90bet_event_id"]."'".')">'.$display_live90bet_x.$p.'</td>';
			$x_toggle = 1;
		} else if ($value["winkel_toto_x"]>=$value["betfair_x"]-0.05 and $value['betfair_x']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["live90bet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotolive90betEvent('."'".$value["live90bet_event_id"]."'".')">'.$display_live90bet_x.$p.'</td>';
			$x_toggle = 1;
		}  else {
			echo '<td class="normal_live90bet" onclick="showno(this,event'.",'".$value["live90bet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotolive90betEvent('."'".$value["live90bet_event_id"]."'".')">'.$display_live90bet_x.$p.'</td>';
		}
	
		//2
		if ($howmanyways===3){
			$p = round($value['live90bet_2']/$value['betfair_2']*100-100,1);
			if ( $p<-99 or $value['betfair_2']<1){
				$p="";
			} else {
				$p = " (".$p."%)";
			//	$p = str_replace("(%)", "", $p);
			}
			if ($value['live90bet_2']==0){
				$value['live90bet_2']="";
		
			}
			$display_live90bet_2 = $value['live90bet_2'] === "" ? "" : number_format((float)$value['live90bet_2'], 2, '.', '');
		if ($value["live90bet_2"]>$value["betfair_2"] and $value['betfair_2']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["live90bet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotolive90betEvent('."'".$value["live90bet_event_id"]."'".')">'.$display_live90bet_2.$p.'</td>';
	$away_toggle = 1;
		} else if ($value["live90bet_2"]>=$value["betfair_2"]-0.05 and $value['betfair_2']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["live90bet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotolive90betEvent('."'".$value["live90bet_event_id"]."'".')">'.$display_live90bet_2.$p.'</td>';
	$away_toggle = 1;
		}  else {
			echo '<td class="normal_live90bet" onclick="showno(this,event'.",'".$value["live90bet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotolive90betEvent('."'".$value["live90bet_event_id"]."'".')">'.$display_live90bet_2.$p.'</td>';
		}
		}
			} else { $home_toggle=0;$x_toggle=0;$away_toggle=0;
		}
		
		//end live90bet

		/* add odds data to table */
		
		//avg book prices

		if ($show_avg==="1"){
			echo '<td class="normal_avg">'.round($value['avg_1'],2)."</td>";
			echo '<td class="normal_avg">'.round($value['avg_x'],2)."</td>";

			if ($howmanyways===3){

				echo '<td class="normal_avg">'.round($value['avg_2'],2)."</td>";

			}
		}
	//end avg book prices

	//UNIBET ODDS
	if ($show_unibet==="1"){
		//ub1
		$p = round($value['unibet_1']/$value['betfair_1']*100-100,1);
		if ( $p<-99 or $value['betfair_1']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
		}
		if ($value['unibet_1']==0){
			$value['unibet_1']="";
	
		}
		if ($value["unibet_1"]>$value["betfair_1"] and $value['betfair_1']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["unibet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoUnibetEvent('.$value["unibet_event_id"].')">'.$value["unibet_1"].$p.'</td>';
	$home_toggle = 1;
		} else if ($value["unibet_1"]>=$value["betfair_1"]-0.05 and $value['betfair_1']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["unibet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoUnibetEvent('.$value["unibet_event_id"].')">'.$value["unibet_1"].$p.'</td>';
	$home_toggle = 1;
		}  else {
			echo '<td class="normal_unibet" onclick="showno(this,event'.",'".$value["unibet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_a."'".')" ondblclick="gotoUnibetEvent('.$value["unibet_event_id"].')">'.$value["unibet_1"].$p.'</td>';
		}
		//ubx
		$p = round($value['unibet_x']/$value['betfair_x']*100-100,1);
		if ( $p<-99 or $value['betfair_x']<1){
			$p="";
		} else {
			$p = " (".$p."%)";
		}
		if ($value['unibet_x']==0){
			$value['unibet_x']="";
	
		}
		if ($value["unibet_x"]>$value["betfair_x"] and $value['betfair_x']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["unibet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoUnibetEvent('.$value["unibet_event_id"].')">'.$value["unibet_x"].$p.'</td>';
	$x_toggle = 1;
		} else if ($value["unibet_x"]>=$value["betfair_x"]-0.05 and $value['betfair_x']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["unibet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoUnibetEvent('.$value["unibet_event_id"].')">'.$value["unibet_x"].$p.'</td>';
	$x_toggle = 1;
		}  else {
			echo '<td class="normal_unibet" onclick="showno(this,event'.",'".$value["unibet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_b."'".')" ondblclick="gotoUnibetEvent('.$value["unibet_event_id"].')">'.$value["unibet_x"].$p.'</td>';
		}
		//ub2
		if ($howmanyways===3){
			$p = round($value['unibet_2']/$value['betfair_2']*100-100,1);
			if ( $p<-99 or $value['betfair_2']<1){
				$p="";
			} else {
				$p = " (".$p."%)";
			}
			if ($value['unibet_2']==0){
				$value['unibet_2']="";
		
			}
		if ($value["unibet_2"]>$value["betfair_2"] and $value['betfair_2']>0) {
			echo '<td class="red" onclick="showno(this,event'.",'".$value["unibet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoUnibetEvent('.$value["unibet_event_id"].')">'.$value["unibet_2"].$p.'</td>';
	$away_toggle = 1;
		} else if ($value["unibet_2"]>=$value["betfair_2"]-0.05 and $value['betfair_2']>0){
				echo '<td class="green" onclick="showno(this,event'.",'".$value["unibet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoUnibetEvent('.$value["unibet_event_id"].')">'.$value["unibet_2"].$p.'</td>';
	$away_toggle = 1;
		}  else {
			echo '<td class="normal_unibet" onclick="showno(this,event'.",'".$value["unibet_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$historical_c."'".')" ondblclick="gotoUnibetEvent('.$value["unibet_event_id"].')">'.$value["unibet_2"].$p.'</td>';
		}
		}
		} else { $home_toggle=0;$x_toggle=0;$away_toggle=0;
		}
	
	
	//betfair1
	if ($home_toggle===1){
echo '<td class="greyed" onclick="showmo(this,event'.",'".$value["betfair_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$bf_historical_a."',".$value['bf_market_p'].','.$value['bf_market_p1'].')" ondblclick="gotoBetfairEvent('.$value["betfair_event_id"].')">'.$value["betfair_1"].'<br>('.$value["betfair_1v"].")<br>(".$value["betfair_1vL"].")<br>".round(100*$value["betfair_1_vwap_perc"],2)."%<br></td>";//$".$value["betfair_1_vwap"]."v $".$value["bf_ltp_1"]."t
	}else{
	echo '<td class="normal_betfair" onclick="showmo(this,event'.",'".$value["betfair_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$bf_historical_a."',".$value['bf_market_p'].','.$value['bf_market_p1'].')" ondblclick="gotoBetfairEvent('.$value["betfair_event_id"].')">'.$value["betfair_1"].'<br>('.$value["betfair_1v"].")<br>(".$value["betfair_1vL"]."<br>".round(100*$value["betfair_1_vwap_perc"],2)."%<br></td>";//$".$value["betfair_1_vwap"]."v $".$value["bf_ltp_1"]."t
	}
	//betfairx
if ($x_toggle===1){

	echo '<td class="greyed" onclick="showmo(this,event'.",'".$value["betfair_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$bf_historical_b."',".$value['bf_market_p'].','.$value['bf_market_p2'].')" ondblclick="gotoBetfairEvent('.$value["betfair_event_id"].')">'.$value["betfair_x"].'<br>('.$value["betfair_xv"].")<br>(".$value["betfair_xvL"].")<br>".round(100*$value["betfair_2_vwap_perc"],2)."%<br></td>";//$".$value["betfair_2_vwap"]."v $".$value["bf_ltp_2"]."t
} else {echo '<td class="normal_betfair" onclick="showmo(this,event'.",'".$value["betfair_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$bf_historical_b."',".$value['bf_market_p'].','.$value['bf_market_p2'].')" ondblclick="gotoBetfairEvent('.$value["betfair_event_id"].')">'.$value["betfair_x"].'<br>('.$value["betfair_xv"].")<br>(".$value["betfair_xvL"].")<br>".round(100*$value["betfair_2_vwap_perc"],2)."%<br></td>";//$".$value["betfair_2_vwap"]."v $".$value["bf_ltp_2"]."t
}
	//betfair2if ($away_toggle===1){
	if ($howmanyways===3){
		if ($away_toggle===1){

		echo '<td class="greyed" onclick="showmo(this,event'.",'".$value["betfair_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$bf_historical_c."',".$value['bf_market_p'].','.$value['bf_market_p3'].')" ondblclick="gotoBetfairEvent('.			$value["betfair_event_id"].')">'.$value["betfair_2"].'<br>('.$value["betfair_2v"].")<br>(".$value["betfair_2vL"].")<br>".round(100*$value["betfair_x_vwap_perc"],2)."%<br></td>";//$".$value["betfair_x_vwap"]."v $".$value["bf_ltp_x"]."t
	}else{
		echo '<td class="normal_betfair" onclick="showmo(this,event'.",'".$value["betfair_event_id"]."','".$value["t1_betfair"]." v ".$value["t2_betfair"]."','".$bf_historical_c."',".$value['bf_market_p'].','.$value['bf_market_p3'].')" ondblclick="gotoBetfairEvent('.$value["betfair_event_id"].')">'.$value["betfair_2"].'<br>('.$value["betfair_2v"].")<br>(".$value["betfair_2vL"].")<br>".round(100*$value["betfair_x_vwap_perc"],2)."%<br></td>";//$".$value["betfair_x_vwap"]."v $".$value["bf_ltp_x"]."t
	}
	}
	
	echo '</tr>';
}
}
//////
echo '</table>';

$end_time = microtime(true);
$elapsed_time = $end_time - $start_time;
//echo "<br>Table took " . $elapsed_time . " seconds to execute.";

echo '<br><br><br><br><br><br><br><br><br><br><br><br>';



?>
