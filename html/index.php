<html>
	<head>
		<title>Message Archive</title>
		<link rel="stylesheet" href="css/styles.css">
	</head>
	<body>
		<div class='header conversation-header'><span class='fn'>Message Archive</span></div>
		<div class='top-space'>&nbsp;</div>
		<?php
			$dbpath = "/data/messages.db";

			$db = new SQLite3($dbpath);

			$sql = "select fn, address from people;";
			$people = $db->query($sql);

			$sql = "select address, strftime('%m/%d/%Y %H:%M', datetime(max(date), 'localtime')) as date, max(date) as sortdate from messages group by address order by sortdate desc;";
			$result = $db->query($sql);
			while ($row = $result->fetchArray()) {
				$addresses = explode(",",$row['address']);
				$displayname = "";
				foreach ($addresses as &$address) {
					$fn = preg_replace('~.*(\d{3})[^\d]{0,7}(\d{3})[^\d]{0,7}(\d{4}).*~', '($1) $2-$3', $address);
					while ($person = $people->fetchArray()) {
						if ($person['address'] == $address && $person['fn'] != $address) {
							$fn = $person['fn'];
						}
					}
					if ($displayname == "")
						$displayname = $fn;
					else
						$displayname = $displayname.", ".$fn;
				}
				$date = $row['date'];
				$hours = (int)substr($date, 11, 2);
				$t = " AM ";
				if ($hours > 12) {
					$t = " PM ";
					$hours = $hours-12;
				}
				$date = substr_replace($date, $t, 16, 1);
				$date = substr_replace($date, $hours, 11, 2);
				echo "<a class='link' href='conversation.php?fn=".urlencode($displayname)."&address=".urlencode($row['address'])."'>";
				echo "<div class='conversation'><span class='fn'>".$displayname."</span> <div class='count'>".$date."</div></div>";
				echo "</a>";
			}
		?>
	</body>
</html>
