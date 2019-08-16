library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;

entity gbt_pattern_checker is
  generic (
    NUM_FRAMES_TO_SYNC : positive := 3
  );
  port (
    clk                     : in std_logic;
    rst_n                   : in std_logic;
    widebus_mode_i          : in std_logic;
    rx_data_i               : in std_logic_vector(83 downto 0);
    rx_extra_data_widebus_i : in std_logic_vector(31 downto 0);
    synced_o                : out std_logic;
    num_of_err_frames_o     : out std_logic_vector(31 downto 0)
  );

  alias sc_ic_rx_data is rx_data_i(83 downto 82);
  alias sc_ec_rx_data is rx_data_i(81 downto 80);
  alias rx_data_0  is rx_data_i(79 downto 60);
  alias rx_data_1  is rx_data_i(59 downto 40);
  alias rx_data_2  is rx_data_i(39 downto 20);
  alias rx_data_3  is rx_data_i(19 downto 0);

  alias rx_extra_data_widebus_0 is rx_extra_data_widebus_i(31 downto 16);
  alias rx_extra_data_widebus_1 is rx_extra_data_widebus_i(15 downto 0);

end gbt_pattern_checker;

architecture behavioral of gbt_pattern_checker is

  signal num_of_err_frames : unsigned(31 downto 0);

  impure function received_correct_data(sc_cnt : in unsigned(1 downto 0);
                                        common_word_cnt : in unsigned(19 downto 0);
                                        widebus_mode : in std_logic;
                                        widebus_word_cnt : in unsigned(15 downto 0))
                                        return boolean is
  begin
    if sc_ic_rx_data /= "11" then
      return false;
    end if;

    if unsigned(sc_ec_rx_data) /= sc_cnt then
      return false;
    end if;

    if unsigned(rx_data_0) /= common_word_cnt or
      rx_data_0 /= rx_data_1 or
      rx_data_0 /= rx_data_2 or
      rx_data_0 /= rx_data_3
    then
      return false;
    end if;

    if widebus_mode = '1' then
      if unsigned(rx_extra_data_widebus_0) /= widebus_word_cnt or
        rx_extra_data_widebus_0 /= rx_extra_data_widebus_1
      then
        return false;
      end if;
    end if;

    return true;
  end;

begin

  process(clk)
    type state_type is (IDLE, SYNCING, RECEIVING);
    variable state : state_type := IDLE;

    variable sync_cnt : natural := 0;

    variable sc_ec_word_cnt   : unsigned( 1 downto 0);
    variable common_word_cnt  : unsigned(19 downto 0);
    variable widebus_word_cnt : unsigned(15 downto 0);
  begin
    if rising_edge(clk) then
      if rst_n = '0' then
        state := IDLE;
        sync_cnt := 0;
        synced_o <= '0';
      else
        case state is
          when IDLE =>
            state := SYNCING;
            num_of_err_frames <= (others => '0');
          when SYNCING =>
            if received_correct_data(sc_ec_word_cnt + 1,
                                     common_word_cnt + 1,
                                     widebus_mode_i,
                                     widebus_word_cnt + 1)
            then
              sync_cnt := sync_cnt + 1;
            else
              sync_cnt := 0;
            end if;

            if sync_cnt = NUM_FRAMES_TO_SYNC then
              state := RECEIVING;
            end if;

            sc_ec_word_cnt := unsigned(sc_ec_rx_data);
            common_word_cnt := unsigned(rx_data_0);
            widebus_word_cnt := unsigned(rx_extra_data_widebus_0);

          when RECEIVING =>
            synced_o <= '1';

            sc_ec_word_cnt := sc_ec_word_cnt + 1;
            common_word_cnt := common_word_cnt + 1;
            widebus_word_cnt := widebus_word_cnt + 1;

            if not received_correct_data(sc_ec_word_cnt,
                                         common_word_cnt,
                                         widebus_mode_i,
                                         widebus_word_cnt)
            then
              num_of_err_frames <= num_of_err_frames + 1;
            end if;
          when others =>
              state := IDLE;
        end case;
      end if;
    end if;
  end process;

  num_of_err_frames_o <= std_logic_vector(num_of_err_frames);

end behavioral;
