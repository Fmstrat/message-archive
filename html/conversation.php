<html>
<?php
	$dbpath = "/data/messages.db";

	$db = new SQLite3($dbpath);

	$sql = "select count(id) as count from messages where address='".$_GET["address"]."'";
	$result = $db->query($sql);
	$count = 0;
	while ($row = $result->fetchArray()) {
		$count = $row['count'];
	}
	$address = $_GET["address"];
	$group = true;
	if (strpos($address,",") === false)
		$group = false;
	$sql = "select ifnull((select fn from people where messages.sender=people.address), messages.sender) as sender, body, img, source, strftime('%m/%d/%Y %H:%M', datetime(date, 'localtime')) as strdate, msgtype from messages where address='".$address."' order by date";
	$result = $db->query($sql);
	$fn = $address;
	if (isset($_GET["fn"]))
		$fn = $_GET["fn"];
	$formattedphone = preg_replace('~.*(\d{3})[^\d]{0,7}(\d{3})[^\d]{0,7}(\d{4}).*~', '($1) $2-$3', $address);
?>
	<head>
		<title><?php echo $fn;?> - Message Archive</title>
		<link rel="stylesheet" href="css/styles.css">
		<script type="text/javascript" src="js/jquery.min.js"></script>
		<script type="text/javascript" src="js/lazyload.js"></script>
	</head>
	<body onload="window.scrollTo(0,document.body.scrollHeight);">
	<?php
		if ($group)
			echo "<div class='header ellipse'><span class='fn'>".$fn."</span><div class='count'>".number_format($count)." <span class='header-label'>messages</span></div></div>";
		else
			echo "<div class='header ellipse'><span class='fn'>".$fn."</span> <span class='header-label'>&#8226; ".$formattedphone."</span><div class='count'>".number_format($count)." <span class='header-label'>messages</span></div></div>";
	?>
	<div class='container'>
	<?php
		$prevclass = "";
		$prevsource = "";
		$prevsender = "";
		$prevsender = "";
		$prevmsgtype = -1;
		echo "<div class='top-space'>&nbsp;</div>";
		$colorcount = 0;
		$colors = [];
		class Color {
			public $color;
			public $address;
		}
		while ($row = $result->fetchArray()) {
			$body = str_replace('img src="', 'img src="NOSHOW-', $row['body']);
			$source = $row['source'];
			$msgtype = $row['msgtype'];
			if ($source == "voice")
				$source = "Google Voice";
			elseif ($source == "hangouts")
				$source = "Hangouts";
			else
				$source = "Signal";
			$date = $row['strdate'];
			$hours = (int)substr($date, 11, 2);
			$t = " AM ";
			if ($hours > 12) {
				$t = " PM ";
				$hours = $hours-12;
			}
			$date = substr_replace($date, $t, 16, 1);
			$date = substr_replace($date, $hours, 11, 2);
			$class = "recipient";
			$sender = " ";
			$curcolor = "";
			if ($msgtype == 2)
				$class = "sender";
			elseif ($group) {
				$sender = preg_replace('~.*(\d{3})[^\d]{0,7}(\d{3})[^\d]{0,7}(\d{4}).*~', '($1) $2-$3', $row["sender"])." &#8226; ";
				foreach ($colors as $color) 
					if ($color->address == $row['sender']) {
						$curcolor = $color->color;
						break;
					}
				if ($curcolor == "") {
					$colorcount++;
					$curcolor = "color".$colorcount;
					$color = new Color();
					$color->color = $curcolor;
					$color->address = $row['sender'];
					$colors[] = $color;
				}
			}
			if (($prevdate != $date && $prevdate != "") || ($prevsource != $source && $prevsource != "") || ($prevsender != $sender && $prevsender != "") || ($prevmsgtype != $msgtype && $prevmsgtype != -1))
				echo "<div class='".$prevclass."-meta'>".$prevsender.$prevdate." (".$prevsource.")</div>";
			if ($prevsender != $sender && $prevsender != "")
				echo "<div style='clear:both'></div>";
				echo "<div class='".$prevclass."-space'>&nbsp;</div>";
			if ($row["img"] != '') {
				$imgfile = "images/voice/".$row["img"];
				if ($row["source"] == "hangouts")
					$imgfile = "images/hangouts/".$row["img"];
				if (!file_exists($imgfile)) {
					$imgfile = str_replace("-1.", "-(1).", $imgfile);
					if (!file_exists($imgfile)) {
						$imgfile = str_replace("-(1).", "-.", $imgfile);
					}
				}
				$img = "<a href='".$imgfile."' target='_new'><img height=200 src='image.gif' class='lazy' data-src='".$imgfile."'></a>";
				echo "<div style='text-align:center' class='talk-bubble round ".$class." ".$curcolor."'><div style='text-align:center' class='talktext'>";
				echo $img;
				echo "</div></div>";
			}
			if ($body != "") {
				echo "<div class='talk-bubble round ".$class." ".$curcolor."'><div class='talktext'>";
				$body = preg_replace('/((http|ftp|https):\/\/[\w-]+(\.[\w-]+)+([\w.,@?^=%&amp;:\/~+#-]*[\w@?^=%&amp;\/~+#-])?)/', '<a style="color: inherit;" href="\1">\1</a>', $body);
				echo $body;
				echo "</div></div>";
			}
			$prevdate = $date;
			$prevclass = $class;
			$prevsource = $source;
			$prevsender = $sender;
			$prevmsgtype = $msgtype;
		}
		if ($prevdate != "")
			echo "<div class='".$prevclass."-meta'>".$prevsender.$prevdate." (".$prevsource.")</div>";
		echo "<div class='sender-space'>&nbsp;</div>";

	?>
	</div>
	</body>
</html>
